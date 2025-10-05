"""常量与枚举定义"""

from enum import Enum


class SyncOperation(str, Enum):
    TEST_CONNECTION = "test_connection"
    SYNC_DEPARTMENTS = "sync_departments"
    SYNC_USERS = "sync_users"
    SYNC_ATTENDANCE = "sync_attendance"
    FULL_SYNC = "full_sync"


class SyncStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 3
BASE_URL = "https://oapi.dingtalk.com"

# 钉钉 webhook 验签 header 名
SIGN_HEADER_TIMESTAMP = "timestamp"
SIGN_HEADER_SIGNATURE = "sign"
SIGN_HEADER_NONCE = "nonce"
