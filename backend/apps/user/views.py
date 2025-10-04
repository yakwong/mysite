import random

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model, authenticate
from django.core.files.storage import default_storage
from django.conf import settings
from uuid import uuid4
import os
from apps.monitor.models import LoginLog
from django.core.cache import cache
from .serializers import (
    UserSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UserSecurityLogSerializer,
    ChangePasswordSerializer,
    SendCodeSerializer,
    PhoneBindingSerializer,
    VerificationCodeSerializer,
    BackupEmailSerializer,
    SecurityQuestionSerializer,
    TwoFactorSerializer,
    LoginNotifierSerializer,
)
from utils.pagination import (
    CustomPageNumberPagination,
    CustomLimitOffsetPagination,
    CustomCursorPagination,
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.utils.timezone import localtime
from utils.response import CustomResponse
from django_filters.rest_framework import DjangoFilterBackend
from .filters import UserFilter
from utils.viewset import CustomModelViewSet
from django.contrib.auth.signals import user_logged_in
from .signals import user_login_failed


def _mask_phone(phone):
    if not phone:
        return None
    return f"{phone[:3]}****{phone[-4:]}"


def _mask_email(email):
    if not email:
        return None
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def _verification_cache_key(user_id: int, action: str) -> str:
    return f"user:security:code:{user_id}:{action}"


def _format_datetime(value):
    if not value:
        return None
    return localtime(value).isoformat()

User = get_user_model()


class UserViewSet(CustomModelViewSet):
    """
    用户视图集，支持用户的CRUD操作
    """

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    pagination_class = CustomPageNumberPagination

    @action(methods=["get", "patch"], detail=False, permission_classes=[IsAuthenticated], url_path="profile")
    def profile(self, request):
        """获取或更新当前登录用户的个人信息"""

        user = request.user
        if request.method.lower() == "get":
            serializer = UserProfileSerializer(user)
            return CustomResponse(success=True, data=serializer.data, msg="成功获取个人信息")

        original_phone = user.phone
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if "phone" in serializer.validated_data and serializer.validated_data.get("phone") != original_phone:
            instance.phone_verified = False
            instance.save(update_fields=["phone_verified"])
            serializer = UserProfileSerializer(instance)
        return CustomResponse(success=True, data=serializer.data, msg="个人信息更新成功")

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="profile/avatar",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_avatar(self, request):
        """上传并更新当前用户头像"""

        file_obj = request.FILES.get("file") or request.FILES.get("avatar")
        if not file_obj:
            return CustomResponse(success=False, data=None, msg="未检测到上传文件", status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(file_obj.name)[1] or ".png"
        filename = f"{uuid4().hex}{ext}"
        save_path = os.path.join("avatars", filename)
        stored_path = default_storage.save(save_path, file_obj)
        avatar_url = default_storage.url(stored_path)

        user = request.user
        # 删除旧头像（仅限存储在媒体目录下的文件）
        old_avatar = user.avatar
        if old_avatar:
            media_url = getattr(settings, "MEDIA_URL", "/media/") or "/media/"
            if old_avatar.startswith(media_url):
                old_relative = old_avatar[len(media_url) :].lstrip("/")
            else:
                old_relative = old_avatar
            try:
                if old_relative and default_storage.exists(old_relative):
                    default_storage.delete(old_relative)
            except Exception:
                pass

        user.avatar = avatar_url
        user.save(update_fields=["avatar"])

        serializer = UserProfileSerializer(user)
        return CustomResponse(success=True, data=serializer.data, msg="头像更新成功")

    @action(methods=["get"], detail=False, permission_classes=[IsAuthenticated], url_path="security-logs")
    def security_logs(self, request):
        """获取当前登录用户的登录日志"""

        user = request.user
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        queryset = LoginLog.objects.filter(username=user.username).order_by("-create_time")
        total = queryset.count()
        start = (page - 1) * limit
        end = start + limit
        serializer = UserSecurityLogSerializer(queryset[start:end], many=True)
        data = {
            "list": serializer.data,
            "total": total,
            "pageSize": limit,
            "currentPage": page,
        }
        return CustomResponse(success=True, data=data, msg="成功获取安全日志")

    @action(
        methods=["post"], detail=False, permission_classes=[IsAuthenticated], url_path="profile/send-code"
    )
    def send_security_code(self, request):
        """发送账户安全相关验证码"""

        serializer = SendCodeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        target = serializer.validated_data.get("target")

        cache_key = _verification_cache_key(request.user.id, action)
        cooldown_key = f"{cache_key}:cooldown"
        if cache.get(cooldown_key):
            return CustomResponse(
                success=False,
                data=None,
                msg="请求过于频繁，请稍后再试",
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        code = f"{random.randint(0, 999999):06d}"
        cache.set(cache_key, {"code": code, "target": target}, timeout=300)
        cache.set(cooldown_key, True, timeout=60)

        response_data = {"expires_in": 300}
        if settings.DEBUG:
            response_data["code"] = code

        return CustomResponse(success=True, data=response_data, msg="验证码发送成功")

    @action(
        methods=["post"], detail=False, permission_classes=[IsAuthenticated], url_path="profile/change-password"
    )
    def change_password(self, request):
        """修改当前用户密码"""

        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.password_strength = serializer.validated_data["password_strength"]
        user.password_updated_at = timezone.now()
        user.save(update_fields=["password", "password_strength", "password_updated_at"])

        return CustomResponse(
            success=True,
            data={
                "password_strength": user.password_strength,
                "password_updated_at": _format_datetime(user.password_updated_at),
            },
            msg="密码修改成功",
        )

    @action(
        methods=["post"], detail=False, permission_classes=[IsAuthenticated], url_path="profile/bind-phone"
    )
    def bind_phone(self, request):
        """绑定手机号"""

        serializer = PhoneBindingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        cache_key = _verification_cache_key(request.user.id, "bind_phone")
        cache_data = cache.get(cache_key)
        if not cache_data or cache_data.get("code") != serializer.validated_data["code"]:
            return CustomResponse(success=False, data=None, msg="验证码错误或已过期", status=status.HTTP_400_BAD_REQUEST)
        if cache_data.get("target") and cache_data["target"] != serializer.validated_data["phone"]:
            return CustomResponse(success=False, data=None, msg="验证码与手机号不匹配", status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.phone = serializer.validated_data["phone"]
        user.phone_verified = True
        user.save(update_fields=["phone", "phone_verified"])
        cache.delete(cache_key)

        data = {
            "phone": user.phone,
            "phone_verified": user.phone_verified,
            "masked_phone": _mask_phone(user.phone),
        }
        return CustomResponse(success=True, data=data, msg="绑定手机号成功")

    @action(
        methods=["post"], detail=False, permission_classes=[IsAuthenticated], url_path="profile/unbind-phone"
    )
    def unbind_phone(self, request):
        """解绑手机号"""

        serializer = VerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cache_key = _verification_cache_key(request.user.id, "unbind_phone")
        cache_data = cache.get(cache_key)
        if not cache_data or cache_data.get("code") != serializer.validated_data["code"]:
            return CustomResponse(success=False, data=None, msg="验证码错误或已过期", status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.phone = None
        user.phone_verified = False
        user.save(update_fields=["phone", "phone_verified"])
        cache.delete(cache_key)

        data = {
            "phone": user.phone,
            "phone_verified": user.phone_verified,
            "masked_phone": _mask_phone(user.phone),
        }
        return CustomResponse(success=True, data=data, msg="解绑手机号成功")

    @action(
        methods=["post", "delete"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="profile/backup-email",
    )
    def backup_email(self, request):
        """设置或解除备用邮箱"""

        user = request.user
        if request.method.lower() == "delete":
            user.backup_email = None
            user.save(update_fields=["backup_email"])
            return CustomResponse(success=True, data={"backup_email": None}, msg="已移除备用邮箱")

        serializer = BackupEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cache_key = _verification_cache_key(user.id, "backup_email")
        cache_data = cache.get(cache_key)
        if not cache_data or cache_data.get("code") != serializer.validated_data["code"]:
            return CustomResponse(success=False, data=None, msg="验证码错误或已过期", status=status.HTTP_400_BAD_REQUEST)
        target = cache_data.get("target")
        if target and target != serializer.validated_data["backup_email"]:
            return CustomResponse(success=False, data=None, msg="验证码与邮箱不匹配", status=status.HTTP_400_BAD_REQUEST)

        user.backup_email = serializer.validated_data["backup_email"]
        user.save(update_fields=["backup_email"])
        cache.delete(cache_key)
        data = {"backup_email": user.backup_email, "masked_backup_email": _mask_email(user.backup_email)}
        return CustomResponse(success=True, data=data, msg="备用邮箱设置成功")

    @action(
        methods=["post", "delete"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="profile/security-question",
    )
    def security_question(self, request):
        """设置或清除密保问题"""

        user = request.user
        if request.method.lower() == "delete":
            user.security_question = None
            user.security_answer_hash = None
            user.security_question_updated_at = None
            user.save(update_fields=["security_question", "security_answer_hash", "security_question_updated_at"])
            return CustomResponse(success=True, data={"security_question_set": False}, msg="已清除密保问题")

        serializer = SecurityQuestionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.create_or_update()
        data = {
            "security_question": user.security_question,
            "security_question_updated_at": _format_datetime(user.security_question_updated_at),
            "security_question_set": True,
        }
        return CustomResponse(success=True, data=data, msg="密保问题设置成功")

    @action(
        methods=["post"], detail=False, permission_classes=[IsAuthenticated], url_path="profile/two-factor"
    )
    def toggle_two_factor(self, request):
        """开启或关闭两步验证"""

        serializer = TwoFactorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.two_factor_enabled = serializer.validated_data["enabled"]
        request.user.save(update_fields=["two_factor_enabled"])
        return CustomResponse(success=True, data={"two_factor_enabled": request.user.two_factor_enabled}, msg="两步验证设置成功")

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="profile/login-notifier",
    )
    def toggle_login_notifier(self, request):
        """开启或关闭登录提醒"""

        serializer = LoginNotifierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.login_notifier_enabled = serializer.validated_data["enabled"]
        request.user.save(update_fields=["login_notifier_enabled"])
        status_text = "登录提醒已开启" if request.user.login_notifier_enabled else "登录提醒已关闭"
        data = {"login_notifier_enabled": request.user.login_notifier_enabled}
        return CustomResponse(success=True, data=data, msg=status_text)

    @action(
        methods=["get"], detail=False, permission_classes=[IsAuthenticated], url_path="profile/security-state"
    )
    def security_state(self, request):
        """获取账户安全概览"""

        user = request.user
        data = {
            "password_strength": user.password_strength,
            "password_updated_at": _format_datetime(user.password_updated_at),
            "phone": user.phone,
            "phone_verified": user.phone_verified,
            "masked_phone": _mask_phone(user.phone),
            "backup_email": user.backup_email,
            "masked_backup_email": _mask_email(user.backup_email),
            "security_question": user.security_question,
            "security_question_set": bool(user.security_question and user.security_answer_hash),
            "security_question_updated_at": _format_datetime(user.security_question_updated_at),
            "two_factor_enabled": user.two_factor_enabled,
            "login_notifier_enabled": user.login_notifier_enabled,
        }
        return CustomResponse(success=True, data=data, msg="成功获取账号安全信息")


class LoginView(APIView):
    """
    登录类，调用auth的认证登录与JWT逻辑
    """

    permission_classes = [AllowAny]  # 该接口不需要任何权限
    authentication_classes = []  # 该接口不需要鉴权

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.validated_data["account"]
            password = serializer.validated_data["password"]
            # 使用自定义认证后端，支持邮箱、用户名、手机号登录
            user = authenticate(request=request, account=account, password=password)
            if user is not None:
                if user.status == 0:
                    return CustomResponse(success=False, msg="用户已被禁用", status=status.HTTP_401_UNAUTHORIZED)
                current_time = timezone.now()
                # 发送登录信号
                user_logged_in.send(sender=user.__class__, request=request, user=user)
                # 生成token
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                # 获取当前时间和过期时间+8小时
                expiration_time = current_time + access_token.lifetime + timezone.timedelta(hours=8)
                expiration_time_str = expiration_time.strftime("%Y/%m/%d %H:%M:%S")
                # 序列化user数据
                userdata = UserSerializer(user).data
                data = {"avatar": userdata["avatar"], "username": userdata["username"], "nickname": userdata["nickname"], "roles": userdata["role"], "refreshToken": str(refresh), "accessToken": str(refresh.access_token), "expires": expiration_time_str}
                return CustomResponse(data=data, msg="登陆成功")

            # 发送登录失败信号
            user_login_failed.send(sender=user.__class__, request=request, email=account)
            return CustomResponse(success=False, msg="登录信息错误", status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
