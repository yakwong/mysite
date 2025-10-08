import re
from typing import Tuple

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from apps.monitor.models import LoginLog
from apps.system.models import Role

User = get_user_model()  # 获取自定义的用户模型


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器，用于创建和检索用户"""

    dept_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), many=True, required=False, default=list)
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "nickname",
            "avatar",
            "phone",
            "phone_verified",
            "backup_email",
            "description",
            "password",
            "status",
            "last_login",
            "password_strength",
            "password_updated_at",
            "security_question",
            "security_question_updated_at",
            "two_factor_enabled",
            "login_notifier_enabled",
            "dept",
            "dept_name",
            "role",
            "role_name",
        )
        extra_kwargs = {"password": {"write_only": True}}  # 设置密码为只写字段

    def get_dept_name(self, obj):
        """获取部门名称"""
        if obj.dept:
            return obj.dept.name  # 假设DeptInfo表中有一个name字段存储部门名称
        return None

    def get_role_name(self, obj):
        """获取角色名称列表"""
        # 返回角色名称列表
        return [role.name for role in obj.role.all()]

    def create(self, validated_data):
        """重写创建方法以使用set_password方法来创建用户；同时处理role字段"""
        password = validated_data.pop("password")
        roles = validated_data.pop("role", [])
        user = User(**validated_data)
        user.set_password(password)  # 使用set_password来设置密码
        user.save()
        user.role.set(roles)  # 设置用户角色
        return user

    def update(self, instance, validated_data):
        """重写更新方法，以便在更新密码时也能使用set_password；同时处理role字段"""
        password = validated_data.pop("password", None)
        roles = validated_data.pop("role", [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        # 更新role多对多字段
        if roles:
            instance.role.set(roles)

        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """账户设置-个人信息"""

    class Meta:
        model = User
        fields = (
            "id",
            "avatar",
            "username",
            "nickname",
            "email",
            "phone",
            "phone_verified",
            "backup_email",
            "description",
            "password_strength",
            "password_updated_at",
            "security_question",
            "security_question_updated_at",
            "two_factor_enabled",
            "login_notifier_enabled",
        )
        read_only_fields = ("username",)
        extra_kwargs = {
            "avatar": {"allow_null": True, "required": False},
            "nickname": {"allow_null": True, "required": False},
            "email": {"required": False},
            "phone": {"allow_null": True, "required": False},
            "phone_verified": {"read_only": True},
            "backup_email": {"read_only": True},
            "description": {"allow_null": True, "required": False},
            "password_strength": {"read_only": True},
            "password_updated_at": {"read_only": True},
            "security_question": {"read_only": True},
            "security_question_updated_at": {"read_only": True},
            "two_factor_enabled": {"read_only": True},
            "login_notifier_enabled": {"read_only": True},
        }


def measure_password_strength(password: str) -> Tuple[str, int]:
    """根据长度和字符复杂度评估密码强度"""

    score = 0
    if len(password) >= 8:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[^A-Za-z0-9]", password):
        score += 1

    if score >= 4 and len(password) >= 12:
        return "strong", score
    if score >= 3:
        return "medium", score
    return "weak", score


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码请求"""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "原密码不正确"})

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})

        if attrs["new_password"] == attrs["old_password"]:
            raise serializers.ValidationError({"new_password": "新密码不能与旧密码相同"})

        strength, score = measure_password_strength(attrs["new_password"])
        if score < 3:
            raise serializers.ValidationError({"new_password": "密码需包含大小写字母、数字或特殊字符中的至少三种"})

        attrs["password_strength"] = strength
        return attrs


class SendCodeSerializer(serializers.Serializer):
    """发送验证码请求"""

    ACTION_CHOICES = (
        ("bind_phone", "bind_phone"),
        ("unbind_phone", "unbind_phone"),
        ("backup_email", "backup_email"),
    )

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    target = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        action = attrs["action"]
        target = attrs.get("target")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if action == "bind_phone":
            if not target:
                raise serializers.ValidationError({"target": "请提供要绑定的手机号"})
            if not re.match(r"^1[3-9]\d{9}$", target):
                raise serializers.ValidationError({"target": "请输入有效的中国大陆手机号"})
            attrs["target"] = target
        if action == "unbind_phone":
            if not user or not user.phone:
                raise serializers.ValidationError({"action": "当前账号未绑定手机号，无需解绑"})
            attrs["target"] = user.phone
        if action == "backup_email":
            if not target:
                raise serializers.ValidationError({"target": "请提供要绑定的邮箱"})
            attrs["target"] = serializers.EmailField().run_validation(target)
        return attrs


class PhoneBindingSerializer(serializers.Serializer):
    """绑定手机号请求"""

    phone = serializers.CharField()
    code = serializers.CharField()

    def validate_phone(self, value):
        if not re.match(r"^1[3-9]\d{9}$", value):
            raise serializers.ValidationError("请输入有效的中国大陆手机号")
        request = self.context["request"]
        user = request.user
        if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("该手机号已被绑定")
        return value


class VerificationCodeSerializer(serializers.Serializer):
    """验证码验证请求"""

    code = serializers.CharField()


class BackupEmailSerializer(serializers.Serializer):
    """绑定备用邮箱请求"""

    backup_email = serializers.EmailField()
    code = serializers.CharField()


class SecurityQuestionSerializer(serializers.Serializer):
    """设置密保问题请求"""

    question = serializers.CharField(max_length=255)
    answer = serializers.CharField(max_length=255)
    current_answer = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if user.security_answer_hash:
            current_answer = attrs.get("current_answer")
            if not current_answer:
                raise serializers.ValidationError({"current_answer": "请先验证当前密保答案"})
            if not check_password(current_answer, user.security_answer_hash):
                raise serializers.ValidationError({"current_answer": "当前密保答案不正确"})
        return attrs

    def create_or_update(self):
        user = self.context["request"].user
        user.security_question = self.validated_data["question"]
        user.security_answer_hash = make_password(self.validated_data["answer"])
        user.security_question_updated_at = timezone.now()
        user.save(update_fields=["security_question", "security_answer_hash", "security_question_updated_at"])
        return user


class TwoFactorSerializer(serializers.Serializer):
    """两步验证开关"""

    enabled = serializers.BooleanField()


class LoginNotifierSerializer(serializers.Serializer):
    """登录提醒开关"""

    enabled = serializers.BooleanField()


class UserSecurityLogSerializer(serializers.ModelSerializer):
    """账户设置-安全日志列表"""

    summary = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    system = serializers.CharField(source="os", read_only=True)
    browser = serializers.CharField(read_only=True)
    operating_time = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = LoginLog
        fields = ("id", "summary", "ip", "address", "system", "browser", "operating_time", "status")

    def get_summary(self, obj):
        return "登录成功" if obj.status else "登录失败"

    def get_address(self, obj):
        # 预留扩展，可结合IP解析归属地
        return "-" if not obj.ip else obj.ip


class LoginSerializer(serializers.Serializer):
    """
    登录序列化器，支持邮箱、用户名、手机号三种方式登录
    """
    account = serializers.CharField(required=True, help_text="邮箱/用户名/手机号")
    password = serializers.CharField(write_only=True, required=True)

    def validate_account(self, value):
        """验证账号格式，统一去除首尾空白"""
        import re

        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("请输入有效的邮箱、用户名或手机号")

        # 中国手机号正则: 1开头，第二位是3-9，共11位
        phone_pattern = r'^1[3-9]\d{9}$'
        # 邮箱正则
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        # 判断是否为手机号
        if re.match(phone_pattern, normalized):
            return normalized
        # 判断是否为邮箱
        if re.match(email_pattern, normalized):
            return normalized
        # 判断是否为用户名 (允许字母、数字、下划线、中文)
        return normalized
