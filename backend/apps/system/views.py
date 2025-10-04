import json

from datetime import datetime, time

from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.response import CustomResponse
from utils.viewset import CustomModelViewSet

from .filters import RoleFilter, MenuFilter, DeptFilter
from .models import (
    DeptInfo,
    DingTalkAttendanceRecord,
    DingTalkConfig,
    DingTalkDepartment,
    DingTalkSyncLog,
    DingTalkUser,
    Menu,
    MenuMeta,
    Role,
)
from .serializers import (
    DeptInfoSerializer,
    DingTalkConfigSerializer,
    DingTalkDepartmentSerializer,
    DingTalkSyncInfoSerializer,
    DingTalkSyncLogSerializer,
    DingTalkAttendanceSerializer,
    DingTalkUserSerializer,
    MenuMetaSerializer,
    MenuSerializer,
    RoleSerializer,
    RouteSerializer,
)
from .services.dingtalk import (
    DingTalkAPIError,
    DingTalkConfigurationError,
    DingTalkDisabledError,
    DingTalkService,
)


class RoleViewSet(CustomModelViewSet):
    """角色表视图集"""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RoleFilter


class MenuViewSet(CustomModelViewSet):
    """菜单/权限视图集"""

    queryset = Menu.objects.all().order_by("meta__rank")
    serializer_class = MenuSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MenuFilter


class MenuMetaViewSet(CustomModelViewSet):
    """菜单meta视图集"""

    queryset = MenuMeta.objects.all()
    serializer_class = MenuMetaSerializer


class DeptInfoViewSet(CustomModelViewSet):
    """部门信息视图集"""

    queryset = DeptInfo.objects.all()
    serializer_class = DeptInfoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeptFilter


class AsyncRoutesView(APIView):
    """动态路由视图"""

    permission_classes = [IsAuthenticated]  # 仅保留登录用户访问权限限制；去除其余默认权限限制

    def get(self, request):
        user = request.user
        roles = user.role.all()
        # 根据用户角色获取所有关联的菜单，避免重复通过 distinct 去重
        menus = Menu.objects.filter(role__in=roles, menu_type=Menu.MenuChoices.MENU, status=True).distinct().order_by("meta__rank")

        # 获取用户关联的所有权限，并按照 parent_id 进行分组
        permissions = Menu.objects.filter(role__in=roles, menu_type=Menu.MenuChoices.PERMISSION, status=True).distinct()
        # 将权限根据 parent_id 进行分组
        permission_dict = {}
        for perm in permissions:
            parent_id = perm.parent_id
            if parent_id not in permission_dict:
                permission_dict[parent_id] = []
            permission_dict[parent_id].append(perm.code)

        serializer = RouteSerializer(menus, many=True, context={"permission_dict": permission_dict})
        # 返回 JSON 响应
        return CustomResponse(success=True, data=serializer.data, msg="成功获取动态路由")


def _handle_dingtalk_exception(service: DingTalkService, operation: str, exc: Exception):
    message = str(exc)
    detail = ""
    response_status = status.HTTP_400_BAD_REQUEST

    if isinstance(exc, DingTalkAPIError):
        detail = json.dumps(getattr(exc, "payload", {}), ensure_ascii=False) if getattr(exc, "payload", None) else ""
        response_status = status.HTTP_502_BAD_GATEWAY
        service.log_failure(operation, message, detail=detail)
    elif isinstance(exc, DingTalkConfigurationError):
        service.log_failure(operation, message)
    elif isinstance(exc, DingTalkDisabledError):
        service.log_failure(operation, message)
    else:
        response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        service.log_failure(operation, message)

    return CustomResponse(success=False, data=None, msg=message, status=response_status)


class DingTalkConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = DingTalkConfig.load()
        data = {
            "config": DingTalkConfigSerializer(config).data,
            "syncInfo": DingTalkSyncInfoSerializer(config).data,
        }
        return CustomResponse(success=True, data=data, msg="成功获取钉钉配置")

    def put(self, request):
        config = DingTalkConfig.load()
        previous_app_key = config.app_key
        previous_app_secret = config.app_secret
        serializer = DingTalkConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if previous_app_key != instance.app_key or previous_app_secret != instance.app_secret:
            instance.access_token = ""
            instance.access_token_expires_at = None
            instance.save(update_fields=["access_token", "access_token_expires_at", "update_time"])

        return CustomResponse(success=True, data=serializer.data, msg="钉钉配置已更新")


class DingTalkSyncInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = DingTalkConfig.load()
        return CustomResponse(success=True, data=DingTalkSyncInfoSerializer(config).data, msg="成功获取同步信息")


class DingTalkTestConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = DingTalkService(DingTalkConfig.load())
        try:
            data = service.test_connection()
            return CustomResponse(success=True, data=data, msg="钉钉连接正常")
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_dingtalk_exception(service, DingTalkSyncLog.Operation.TEST_CONNECTION, exc)


class DingTalkSyncDepartmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = DingTalkService(DingTalkConfig.load())
        try:
            data = service.sync_departments()
            return CustomResponse(success=True, data=data, msg="部门同步完成")
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_dingtalk_exception(service, DingTalkSyncLog.Operation.SYNC_DEPARTMENTS, exc)


class DingTalkSyncUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = DingTalkService(DingTalkConfig.load())
        try:
            data = service.sync_users()
            return CustomResponse(success=True, data=data, msg="用户同步完成")
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_dingtalk_exception(service, DingTalkSyncLog.Operation.SYNC_USERS, exc)


class DingTalkFullSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = DingTalkService(DingTalkConfig.load())
        try:
            data = service.full_sync()
            return CustomResponse(success=True, data=data, msg="全量同步完成")
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_dingtalk_exception(service, DingTalkSyncLog.Operation.FULL_SYNC, exc)


class DingTalkSyncAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = DingTalkService(DingTalkConfig.load())
        try:
            start = request.data.get("start")
            end = request.data.get("end")
            if not start or not end:
                return CustomResponse(success=False, data=None, msg="请提供 start 和 end 时间", status=status.HTTP_400_BAD_REQUEST)
            try:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
            except ValueError:
                return CustomResponse(success=False, data=None, msg="时间格式需满足 ISO8601", status=status.HTTP_400_BAD_REQUEST)
            if start_dt.tzinfo is None:
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
            if end_dt.tzinfo is None:
                end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())
            if start_dt.date() == end_dt.date():
                # 防止同一天但时间缺省导致 0 区间
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            data = service.sync_attendance(start_dt, end_dt)
            return CustomResponse(success=True, data=data, msg="考勤同步完成")
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_dingtalk_exception(service, DingTalkSyncLog.Operation.SYNC_ATTENDANCE, exc)


class DingTalkSyncLogViewSet(CustomModelViewSet):
    """钉钉同步日志视图"""

    queryset = DingTalkSyncLog.objects.all()
    serializer_class = DingTalkSyncLogSerializer
    http_method_names = ["get", "head", "options"]


class DingTalkDepartmentViewSet(CustomModelViewSet):
    """钉钉部门数据视图"""

    queryset = DingTalkDepartment.objects.all().order_by("dept_id")
    serializer_class = DingTalkDepartmentSerializer
    http_method_names = ["get", "head", "options"]

    def list(self, request, *args, **kwargs):
        source = request.query_params.get("source")
        if source == "remote":
            service = DingTalkService(DingTalkConfig.load())
            try:
                root_dept_id = int(request.query_params.get("root_dept_id", 1))
            except (TypeError, ValueError):
                root_dept_id = 1
            try:
                departments = service.preview_departments(root_dept_id=root_dept_id)
            except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
                return _handle_dingtalk_exception(service, DingTalkSyncLog.Operation.SYNC_DEPARTMENTS, exc)

            total = len(departments)
            limit_param = request.query_params.get("limit")
            try:
                limit_value = int(limit_param) if limit_param is not None else total
            except ValueError:
                limit_value = total
            if limit_value is None or limit_value <= 0:
                limit_value = total
            limit_value = min(max(limit_value, 0), 200)
            preview = departments[:limit_value] if limit_value else []
            return CustomResponse(
                success=True,
                data=preview,
                msg="成功获取实时部门列表",
                page=1,
                limit=limit_value,
                total=total,
            )

        return super().list(request, *args, **kwargs)


class DingTalkUserViewSet(CustomModelViewSet):
    """钉钉用户数据视图"""

    queryset = DingTalkUser.objects.all().order_by("userid")
    serializer_class = DingTalkUserSerializer
    http_method_names = ["get", "head", "options"]


class DingTalkAttendanceViewSet(CustomModelViewSet):
    """钉钉考勤记录视图"""

    queryset = DingTalkAttendanceRecord.objects.all()
    serializer_class = DingTalkAttendanceSerializer
    http_method_names = ["get", "head", "options"]
