"""常量与枚举定义"""

from enum import Enum


class SyncOperation(str, Enum):
    TEST_CONNECTION = "test_connection"
    SYNC_DEPARTMENTS = "sync_departments"
    SYNC_USERS = "sync_users"
    SYNC_DIMISSION_USERS = "sync_dimission_users"
    SYNC_ATTENDANCE = "sync_attendance"
    FULL_SYNC = "full_sync"


class SyncStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 3
BASE_URL = "https://oapi.dingtalk.com"
OPEN_API_BASE_URL = "https://api.dingtalk.com"

# 离职人员同步默认花名册字段（可通过配置覆盖）
DEFAULT_DIMISSION_ROSTER_FIELDS = (
    "sys00-name",
    "sys00-mobile",
    "sys00-jobNumber",
    "sys00-employeeId",
    "sys00-mainDept",
    "sys00-mainDeptId",
    "sys00-dept",
    "sys00-email",
    "sys00-position",
    "sys00-entryDate",
)

# 钉钉 webhook 验签 header 名
SIGN_HEADER_TIMESTAMP = "timestamp"
SIGN_HEADER_SIGNATURE = "sign"
SIGN_HEADER_NONCE = "nonce"

# 考勤打卡类型映射
ATTENDANCE_CHECK_TYPE_LABELS = {
    "OnDuty": "上班打卡",
    "OffDuty": "下班打卡",
}

# 考勤结果映射
ATTENDANCE_TIME_RESULT_LABELS = {
    "Normal": "正常",
    "Early": "早退",
    "Late": "迟到",
    "SeriousLate": "严重迟到",
    "Absenteeism": "旷工",
    "NotSigned": "缺卡",
}
