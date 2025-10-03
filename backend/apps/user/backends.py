"""
自定义认证后端
支持使用邮箱、用户名、手机号三种方式登录
"""
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class MultiFieldAuthBackend(ModelBackend):
    """
    支持多字段认证的后端
    允许使用 email、username 或 phone 登录
    """

    def authenticate(self, request, account=None, password=None, **kwargs):
        """
        重写认证方法，支持多种登录方式

        Args:
            request: HTTP 请求对象
            account: 账号 (可以是 email、username 或 phone)
            password: 密码
            **kwargs: 其他参数

        Returns:
            User: 认证成功返回用户对象，失败返回 None
        """
        if account is None or password is None:
            return None

        # 判断账号类型
        account_type = self._detect_account_type(account)

        # 根据账号类型查询用户
        try:
            if account_type == 'email':
                user = User.objects.get(email=account)
            elif account_type == 'phone':
                user = User.objects.get(phone=account)
            elif account_type == 'username':
                user = User.objects.get(username=account)
            else:
                # 无法识别账号类型，尝试多字段匹配
                user = User.objects.filter(
                    Q(email=account) | Q(username=account) | Q(phone=account)
                ).first()

                if user is None:
                    return None

        except User.DoesNotExist:
            # 用户不存在
            return None

        # 验证密码
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def _detect_account_type(self, account):
        """
        检测账号类型

        Args:
            account: 账号字符串

        Returns:
            str: 'email', 'phone', 'username' 或 'unknown'
        """
        # 中国手机号正则: 1开头，第二位是3-9，共11位
        phone_pattern = r'^1[3-9]\d{9}$'

        # 邮箱正则
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if re.match(phone_pattern, account):
            return 'phone'
        elif re.match(email_pattern, account):
            return 'email'
        else:
            return 'username'

    def user_can_authenticate(self, user):
        """
        检查用户是否可以认证
        重写此方法以检查用户的 status 字段
        """
        is_active = getattr(user, 'status', None)
        return is_active if is_active is not None else True
