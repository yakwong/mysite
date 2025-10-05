class DingTalkAPIError(Exception):
    """钉钉接口调用异常"""

    def __init__(self, message: str, payload: dict | None = None):
        super().__init__(message)
        self.payload = payload or {}


class DingTalkConfigurationError(Exception):
    """钉钉配置缺失或不合法"""


class DingTalkDisabledError(Exception):
    """钉钉集成未启用"""
