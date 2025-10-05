"""DingTalk integration app."""

__all__ = [
    "default_app_config",
]

# Django 3.2+ 自动使用 AppConfig，但为了向后兼容导出字符串
default_app_config = "apps.dingtalk.apps.DingTalkConfig"
