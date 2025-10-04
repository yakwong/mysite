"""钉钉服务封装"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from ..models import (
    DingTalkAttendanceRecord,
    DingTalkConfig,
    DingTalkDepartment,
    DingTalkSyncLog,
    DingTalkUser,
)

logger = logging.getLogger(__name__)


class DingTalkAPIError(Exception):
    """钉钉接口调用异常"""

    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.payload = payload or {}


class DingTalkConfigurationError(ImproperlyConfigured):
    """钉钉配置缺失"""


class DingTalkDisabledError(Exception):
    """钉钉集成被禁用"""


class DingTalkClient:
    """钉钉开放平台客户端"""

    BASE_URL = "https://oapi.dingtalk.com"

    def __init__(self, config: DingTalkConfig):
        self.config = config
        if not self.config.app_key or not self.config.app_secret:
            raise DingTalkConfigurationError("请先完成钉钉App Key与App Secret配置")

    def _build_url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        params = params or {}
        query_string = urlencode({k: v for k, v in params.items() if v is not None})
        if query_string:
            return f"{self.BASE_URL}{path}?{query_string}"
        return f"{self.BASE_URL}{path}"

    def _request(
        self,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        params = params.copy() if params else {}
        if access_token:
            params.setdefault("access_token", access_token)
        url = self._build_url(path, params)
        headers = {"Content-Type": "application/json;charset=utf-8"}
        payload = None
        if data is not None:
            payload = json.dumps(data).encode("utf-8")

        request = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:  # pragma: no cover - network layer不易复现
            detail = exc.read().decode("utf-8") if exc.fp else exc.reason
            raise DingTalkAPIError(f"钉钉接口HTTP错误: {exc.code} - {detail}") from exc
        except URLError as exc:  # pragma: no cover - 同上
            raise DingTalkAPIError(f"钉钉接口网络异常: {exc.reason}") from exc

        try:
            payload_data = json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise DingTalkAPIError("钉钉接口返回格式异常", payload={"raw": body}) from exc

        if not isinstance(payload_data, dict):
            raise DingTalkAPIError("钉钉接口返回格式异常", payload={"raw": payload_data})

        errcode = payload_data.get("errcode")
        if errcode not in (0, None):
            errmsg = payload_data.get("errmsg", "钉钉接口调用失败")
            raise DingTalkAPIError(f"{errmsg}(errcode={errcode})", payload=payload_data)

        return payload_data

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        """获取并缓存access_token"""

        if not force_refresh and self.config.access_token and self.config.access_token_expires_at:
            if self.config.access_token_expires_at - timezone.now() > timedelta(minutes=2):
                return self.config.access_token

        response = self._request(
            "/gettoken",
            params={
                "appkey": self.config.app_key,
                "appsecret": self.config.app_secret,
            },
        )
        access_token = response.get("access_token", "")
        expires_in = int(response.get("expires_in", 7200))
        expires_at = timezone.now() + timedelta(seconds=max(expires_in - 60, 60))
        self.config.access_token = access_token
        self.config.access_token_expires_at = expires_at
        self.config.save(update_fields=["access_token", "access_token_expires_at", "update_time"])
        return access_token

    def get_department(self, dept_id: int) -> Dict[str, Any]:
        access_token = self.get_access_token()
        response = self._request(
            "/topapi/v2/department/get",
            method="POST",
            data={"dept_id": dept_id, "language": "zh_CN"},
            access_token=access_token,
        )
        result = response.get("result")
        return result if isinstance(result, dict) else {}

    def list_departments(self, root_dept_id: int = 1) -> List[Dict[str, Any]]:
        access_token = self.get_access_token()
        visited: set[int] = set()
        results: List[Dict[str, Any]] = []

        def _walk(dept_id: int) -> None:
            payload = self._request(
                "/topapi/v2/department/listsub",
                method="POST",
                data={"dept_id": dept_id, "language": "zh_CN"},
                access_token=access_token,
            )
            result_obj = payload.get("result")
            if isinstance(result_obj, dict):
                dept_list = result_obj.get("dept_list") or []
            elif isinstance(result_obj, list):
                dept_list = result_obj
            else:
                dept_list = []
            for dept in dept_list:
                if not isinstance(dept, dict):
                    continue
                child_dept_id = dept.get("dept_id")
                if child_dept_id is None or child_dept_id in visited:
                    continue
                visited.add(child_dept_id)
                results.append(dept)
                _walk(child_dept_id)

        root_info = self.get_department(root_dept_id)
        if root_info:
            root_id = root_info.get("dept_id", root_dept_id)
            visited.add(root_id)
            results.append(root_info)
            _walk(root_id)
        else:
            _walk(root_dept_id)

        return results

    def list_users_by_dept(self, dept_id: int, size: int = 100) -> List[Dict[str, Any]]:
        access_token = self.get_access_token()
        cursor = 0
        results: List[Dict[str, Any]] = []
        while True:
            payload = self._request(
                "/topapi/v2/user/list",
                method="POST",
                data={
                    "dept_id": dept_id,
                    "cursor": cursor,
                    "size": size,
                    "language": "zh_CN",
                },
                access_token=access_token,
            )
            result_data = payload.get("result") or {}
            user_list = result_data.get("list") or []
            results.extend(user_list)
            next_cursor = result_data.get("next_cursor")
            if not next_cursor:
                break
            cursor = next_cursor
        return results

    def list_all_users(self, dept_ids: Iterable[int]) -> List[Dict[str, Any]]:
        aggregated: Dict[str, Dict[str, Any]] = {}
        for dept_id in dept_ids:
            users = self.list_users_by_dept(dept_id)
            for user in users:
                userid = user.get("userid")
                if not userid:
                    continue
                current = aggregated.get(userid)
                if current:
                    dept_id_list = set(current.get("dept_id_list") or [])
                    dept_id_list.update(user.get("dept_id_list") or [])
                    current["dept_id_list"] = sorted(dept_id_list)
                    current.update({k: v for k, v in user.items() if v not in (None, "")})
                else:
                    aggregated[userid] = user
        return list(aggregated.values())

    def list_attendance_records(
        self,
        userids: Iterable[str],
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict[str, Any]]:
        access_token = self.get_access_token()
        user_list = list(userids)
        if not user_list:
            return []
        # 钉钉接口限制每次最多 50 个用户
        batch_size = 50
        results: List[Dict[str, Any]] = []
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        for index in range(0, len(user_list), batch_size):
            batch = user_list[index : index + batch_size]
            payload = self._request(
                "/topapi/attendance/listRecord",
                method="POST",
                data={
                    "userIdList": batch,
                    "checkDateFrom": start_str,
                    "checkDateTo": end_str,
                    "isI18n": False,
                },
                access_token=access_token,
            )
            result_obj = payload.get("recordresult")
            if isinstance(result_obj, list):
                records = result_obj
            else:
                records = payload.get("result", {}).get("recordresult", [])
            if not isinstance(records, list):
                records = []
            results.extend(records)
        return results


class DingTalkService:
    """钉钉业务封装"""

    def __init__(self, config: Optional[DingTalkConfig] = None):
        self.config = config or DingTalkConfig.load()
        self._client: Optional[DingTalkClient] = None

    def _ensure_client(self) -> DingTalkClient:
        if self._client is None:
            self._client = DingTalkClient(self.config)
        return self._client

    def _ensure_enabled(self) -> None:
        if not self.config.enabled:
            raise DingTalkDisabledError("钉钉集成未启用，请先开启")

    def _record_log(
        self,
        operation: str,
        status: str,
        message: str = "",
        detail: str = "",
        stats: Optional[Dict[str, Any]] = None,
    ) -> DingTalkSyncLog:
        log = DingTalkSyncLog.objects.create(
            operation=operation,
            status=status,
            message=message,
            detail=detail,
            stats=stats or {},
        )
        logger.info("DingTalk %s %s: %s", operation, status, message)
        return log

    def _update_sync_state(
        self,
        *,
        status: str,
        message: str,
        stats: Optional[Dict[str, Any]] = None,
        user_sync_time: Optional[datetime] = None,
        dept_sync_time: Optional[datetime] = None,
        attendance_sync_time: Optional[datetime] = None,
    ) -> None:
        stats = stats or {}
        fields = ["last_sync_status", "last_sync_message", "update_time"]
        self.config.last_sync_status = status
        self.config.last_sync_message = message
        self.config.last_sync_time = timezone.now()
        fields.append("last_sync_time")
        if "user_count" in stats:
            self.config.last_user_sync_count = stats["user_count"]
            fields.append("last_user_sync_count")
        if "dept_count" in stats:
            self.config.last_dept_sync_count = stats["dept_count"]
            fields.append("last_dept_sync_count")
        if "attendance_count" in stats:
            self.config.last_attendance_sync_count = stats["attendance_count"]
            fields.append("last_attendance_sync_count")
        if user_sync_time:
            self.config.last_user_sync_time = user_sync_time
            fields.append("last_user_sync_time")
        if dept_sync_time:
            self.config.last_dept_sync_time = dept_sync_time
            fields.append("last_dept_sync_time")
        if attendance_sync_time:
            self.config.last_attendance_sync_time = attendance_sync_time
            fields.append("last_attendance_sync_time")
        self.config.save(update_fields=list(set(fields)))

    def log_failure(
        self,
        operation: str,
        message: str,
        *,
        detail: str = "",
        stats: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._record_log(
            operation,
            DingTalkSyncLog.Status.FAILED,
            message=message,
            detail=detail,
            stats=stats,
        )
        self._update_sync_state(
            status=DingTalkSyncLog.Status.FAILED,
            message=message,
            stats=stats,
        )

    def test_connection(self) -> Dict[str, Any]:
        client = self._ensure_client()
        token = client.get_access_token(force_refresh=True)
        expires_at = self.config.access_token_expires_at
        expires_iso = expires_at.isoformat() if expires_at else None
        stats = {
            "expires_at": expires_iso,
        }
        self._record_log(
            DingTalkSyncLog.Operation.TEST_CONNECTION,
            DingTalkSyncLog.Status.SUCCESS,
            message="钉钉连接测试成功",
            stats=stats,
        )
        return {"accessToken": token, "expiresAt": expires_iso}

    def preview_departments(self, root_dept_id: int = 1) -> List[Dict[str, Any]]:
        """实时获取钉钉部门列表，用于接口连通性验证。"""
        self._ensure_enabled()
        client = self._ensure_client()
        return client.list_departments(root_dept_id)

    def sync_departments(self) -> Dict[str, Any]:
        self._ensure_enabled()
        client = self._ensure_client()
        departments = client.list_departments()
        synced_ids = set()
        now = timezone.now()
        with transaction.atomic():
            for dept in departments:
                dept_id = dept.get("dept_id")
                if dept_id is None:
                    continue
                defaults = {
                    "name": dept.get("name", ""),
                    "parent_id": dept.get("parent_id"),
                    "order": dept.get("order"),
                    "leader_userid": dept.get("leader_userid", ""),
                    "dept_type": dept.get("dept_tag", ""),
                    "source_info": dept,
                }
                DingTalkDepartment.objects.update_or_create(
                    dept_id=dept_id,
                    defaults=defaults,
                )
                synced_ids.add(dept_id)
        # 清理已经不存在的部门
        stale_ids = set(DingTalkDepartment.objects.values_list("dept_id", flat=True)) - synced_ids
        if stale_ids:
            DingTalkDepartment.objects.filter(dept_id__in=stale_ids).delete()

        stats = {"dept_count": len(synced_ids)}
        message = f"成功同步 {len(synced_ids)} 个部门"
        self._record_log(
            DingTalkSyncLog.Operation.SYNC_DEPARTMENTS,
            DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
        )
        self._update_sync_state(
            status=DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
            dept_sync_time=now,
        )
        return {"count": len(synced_ids)}

    def sync_users(self) -> Dict[str, Any]:
        self._ensure_enabled()
        client = self._ensure_client()
        dept_ids = list(DingTalkDepartment.objects.values_list("dept_id", flat=True))
        if not dept_ids:
            dept_ids = [1]
        users = client.list_all_users(dept_ids)
        synced_ids = set()
        now = timezone.now()
        with transaction.atomic():
            for user in users:
                userid = user.get("userid")
                if not userid:
                    continue
                defaults = {
                    "name": user.get("name", ""),
                    "mobile": user.get("mobile", ""),
                    "email": user.get("email", ""),
                    "active": user.get("active", True),
                    "job_number": user.get("job_number", ""),
                    "title": user.get("title", ""),
                    "dept_ids": user.get("dept_id_list") or [],
                    "unionid": user.get("unionid", ""),
                    "remark": user.get("remark", ""),
                    "source_info": user,
                }
                DingTalkUser.objects.update_or_create(userid=userid, defaults=defaults)
                synced_ids.add(userid)
        stale_ids = set(DingTalkUser.objects.values_list("userid", flat=True)) - synced_ids
        if stale_ids:
            DingTalkUser.objects.filter(userid__in=stale_ids).delete()

        stats = {"user_count": len(synced_ids)}
        message = f"成功同步 {len(synced_ids)} 个用户"
        self._record_log(
            DingTalkSyncLog.Operation.SYNC_USERS,
            DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
        )
        self._update_sync_state(
            status=DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
            user_sync_time=now,
        )
        return {"count": len(synced_ids)}

    def sync_attendance(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        self._ensure_enabled()
        if start_time > end_time:
            raise DingTalkAPIError("开始时间不能晚于结束时间")

        userids = list(DingTalkUser.objects.values_list("userid", flat=True))
        if not userids:
            # 若尚未同步用户，则先执行一次用户同步以确保覆盖所有人员
            self.sync_users()
            userids = list(DingTalkUser.objects.values_list("userid", flat=True))
        if not userids:
            return {"count": 0}

        client = self._ensure_client()
        records = client.list_attendance_records(userids, start_time, end_time)
        synced_ids = set()
        with transaction.atomic():
            for record in records:
                if not isinstance(record, dict):
                    continue
                userid = record.get("userid") or record.get("userId")
                user_check_time = record.get("user_check_time") or record.get("userCheckTime")
                if not userid or not user_check_time:
                    continue
                try:
                    check_dt = datetime.fromisoformat(user_check_time.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        check_dt = datetime.strptime(user_check_time, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                record_id = record.get("record_id") or record.get("recordId")
                if not record_id:
                    record_id = f"{userid}_{check_dt.timestamp()}"
                work_date_raw = record.get("work_date") or record.get("workDate")
                work_date = None
                if work_date_raw:
                    try:
                        work_date = datetime.fromisoformat(str(work_date_raw).replace("Z", "+00:00")).date()
                    except ValueError:
                        try:
                            work_date = datetime.strptime(str(work_date_raw), "%Y-%m-%d").date()
                        except ValueError:
                            work_date = None
                defaults = {
                    "userid": userid,
                    "check_type": record.get("check_type") or record.get("checkType", ""),
                    "time_result": record.get("time_result") or record.get("timeResult", ""),
                    "user_check_time": check_dt,
                    "work_date": work_date,
                    "source_type": record.get("source_type") or record.get("sourceType", ""),
                    "source_info": record,
                }
                DingTalkAttendanceRecord.objects.update_or_create(record_id=record_id, defaults=defaults)
                synced_ids.add(record_id)

        stats = {"attendance_count": len(synced_ids)}
        message = f"成功同步 {len(synced_ids)} 条考勤记录"
        self._record_log(
            DingTalkSyncLog.Operation.SYNC_ATTENDANCE,
            DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
        )
        self._update_sync_state(
            status=DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
            attendance_sync_time=end_time,
        )
        return {"count": len(synced_ids)}

    def full_sync(self) -> Dict[str, Any]:
        dept_result = self.sync_departments()
        user_result = self.sync_users()
        stats = {
            "dept_count": dept_result.get("count", 0),
            "user_count": user_result.get("count", 0),
        }
        message = (
            f"全量同步完成，部门 {stats['dept_count']} 个，用户 {stats['user_count']} 个"
        )
        self._record_log(
            DingTalkSyncLog.Operation.FULL_SYNC,
            DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
        )
        self._update_sync_state(
            status=DingTalkSyncLog.Status.SUCCESS,
            message=message,
            stats=stats,
        )
        return stats
