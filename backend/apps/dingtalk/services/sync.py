from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List

from django.db import transaction
from django.utils import timezone

from ..constants import SyncOperation, SyncStatus
from ..models import (
    DingTalkAttendanceRecord,
    DingTalkConfig,
    DingTalkDepartment,
    DingTalkDimissionUser,
    DingTalkSyncLog,
    DingTalkUser,
    SyncCursor,
)
from ..serializers import DingTalkAttendancePreviewSerializer
from ..signals import post_sync, pre_sync, sync_failed
from .client import DingTalkClient
from .exceptions import DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError
from .mappers import map_attendance, map_department, map_dimission, map_user

logger = logging.getLogger(__name__)


class SyncService:
    """钉钉同步业务逻辑"""

    def __init__(self, config: DingTalkConfig | None = None) -> None:
        self.config = config or DingTalkConfig.load()
        self._client: DingTalkClient | None = None

    # --------------------------- 工具方法 --------------------------- #
    @property
    def client(self) -> DingTalkClient:
        if self._client is None:
            self._client = DingTalkClient(self.config)
        return self._client

    def ensure_enabled(self) -> None:
        if not self.config.enabled:
            raise DingTalkDisabledError("钉钉集成未启用，请先开启")

    def _record_log(
        self,
        operation: SyncOperation,
        status: SyncStatus,
        *,
        message: str = "",
        detail: str = "",
        stats: dict | None = None,
        level: str = "info",
    ) -> DingTalkSyncLog:
        log = DingTalkSyncLog.objects.create(
            operation=operation.value,
            status=status.value,
            message=message,
            detail=detail,
            stats=stats or {},
            level=level,
            config=self.config,
        )
        return log

    def _update_sync_state(
        self,
        *,
        status: SyncStatus,
        message: str,
        stats: dict | None = None,
        user_sync_time: datetime | None = None,
        dept_sync_time: datetime | None = None,
        attendance_sync_time: datetime | None = None,
        dimission_sync_time: datetime | None = None,
    ) -> None:
        self.config.update_sync_state(
            status=status.value,
            message=message,
            stats=stats,
            user_sync_time=user_sync_time,
            dept_sync_time=dept_sync_time,
            attendance_sync_time=attendance_sync_time,
            dimission_sync_time=dimission_sync_time,
        )

    def _handle_failure(
        self,
        operation: SyncOperation,
        exc: Exception,
        *,
        stats: dict | None = None,
        detail: str = "",
    ) -> None:
        message = str(exc)
        level = "error"
        if isinstance(exc, DingTalkAPIError):
            detail = detail or (str(exc.payload) if getattr(exc, "payload", None) else "")
        elif isinstance(exc, DingTalkConfigurationError):
            level = "warning"
        log = self._record_log(
            operation,
            SyncStatus.FAILED,
            message=message,
            detail=detail,
            stats=stats,
            level=level,
        )
        self._update_sync_state(status=SyncStatus.FAILED, message=message, stats=stats)
        sync_failed.send(sender=self.__class__, config=self.config, operation=operation.value, log=log, exception=exc)

    # --------------------------- 对外接口 --------------------------- #
    def test_connection(self, *, force_refresh: bool = True) -> dict:
        pre_sync.send(sender=self.__class__, config=self.config, operation=SyncOperation.TEST_CONNECTION.value)
        try:
            token = self.client.get_access_token(force_refresh=force_refresh)
            expires_at = self.config.access_token_expires_at
            stats = {"expires_at": expires_at.isoformat() if expires_at else None}
            self._record_log(
                SyncOperation.TEST_CONNECTION,
                SyncStatus.SUCCESS,
                message="钉钉连接测试成功",
                stats=stats,
            )
            post_sync.send(
                sender=self.__class__,
                config=self.config,
                operation=SyncOperation.TEST_CONNECTION.value,
                stats=stats,
            )
            return {"accessToken": token, "expiresAt": stats["expires_at"]}
        except Exception as exc:  # pragma: no cover - 异常路径在测试覆盖
            self._handle_failure(SyncOperation.TEST_CONNECTION, exc)
            raise

    def sync_departments(self, *, mode: str = "full") -> dict:
        self.ensure_enabled()
        pre_sync.send(sender=self.__class__, config=self.config, operation=SyncOperation.SYNC_DEPARTMENTS.value)
        try:
            departments = self.client.list_departments()
            synced_ids: set[int] = set()
            now = timezone.now()
            with transaction.atomic():
                for dept in departments:
                    dept_id = dept.get("dept_id")
                    if dept_id is None:
                        continue
                    defaults = map_department(self.config.id, dept)
                    DingTalkDepartment.objects.update_or_create(dept_id=dept_id, defaults=defaults)
                    synced_ids.add(dept_id)
            stale_queryset = DingTalkDepartment.objects.filter(config=self.config).exclude(dept_id__in=synced_ids)
            stale_count = stale_queryset.count()
            if stale_count:
                stale_queryset.delete()

            stats = {"dept_count": len(synced_ids), "stale_count": stale_count, "mode": mode}
            message = f"同步部门完成 ({len(synced_ids)} 个)"
            self._record_log(
                SyncOperation.SYNC_DEPARTMENTS,
                SyncStatus.SUCCESS,
                message=message,
                stats=stats,
            )
            self._update_sync_state(
                status=SyncStatus.SUCCESS,
                message=message,
                stats=stats,
                dept_sync_time=now,
            )
            post_sync.send(
                sender=self.__class__,
                config=self.config,
                operation=SyncOperation.SYNC_DEPARTMENTS.value,
                stats=stats,
            )
            return {"count": len(synced_ids), "staleCount": stale_count}
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(SyncOperation.SYNC_DEPARTMENTS, exc)
            raise

    def _get_dept_ids_for_user_sync(self) -> List[int]:
        dept_ids = list(DingTalkDepartment.objects.filter(config=self.config).values_list("dept_id", flat=True))
        if not dept_ids:
            dept_ids = [1]
        return dept_ids

    def sync_users(self, *, mode: str = "full") -> dict:
        self.ensure_enabled()
        pre_sync.send(sender=self.__class__, config=self.config, operation=SyncOperation.SYNC_USERS.value)
        try:
            dept_ids = self._get_dept_ids_for_user_sync()
            users = self.client.list_all_users(dept_ids)
            synced_ids: set[str] = set()
            now = timezone.now()
            with transaction.atomic():
                for user in users:
                    userid = user.get("userid")
                    if not userid:
                        continue
                    defaults = map_user(self.config.id, user)
                    DingTalkUser.objects.update_or_create(userid=userid, defaults=defaults)
                    synced_ids.add(userid)
            stale_queryset = DingTalkUser.objects.filter(config=self.config).exclude(userid__in=synced_ids)
            stale_count = stale_queryset.count()
            if stale_count:
                stale_queryset.delete()

            stats = {"user_count": len(synced_ids), "stale_count": stale_count, "mode": mode}
            message = f"同步用户完成 ({len(synced_ids)} 个)"
            self._record_log(
                SyncOperation.SYNC_USERS,
                SyncStatus.SUCCESS,
                message=message,
                stats=stats,
            )
            self._update_sync_state(
                status=SyncStatus.SUCCESS,
                message=message,
                stats=stats,
                user_sync_time=now,
            )
            post_sync.send(
                sender=self.__class__,
                config=self.config,
                operation=SyncOperation.SYNC_USERS.value,
                stats=stats,
            )
            return {"count": len(synced_ids), "staleCount": stale_count}
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(SyncOperation.SYNC_USERS, exc)
            raise

    def sync_dimission_users(self, *, mode: str = "full") -> dict:
        self.ensure_enabled()
        pre_sync.send(sender=self.__class__, config=self.config, operation=SyncOperation.SYNC_DIMISSION_USERS.value)
        try:
            userids = self.client.list_dimission_userids()
            details = self.client.list_dimission_infos(userids)
            detail_map = {}
            for item in details:
                if not isinstance(item, dict):
                    continue
                userid = str(item.get("userid") or "")
                if userid:
                    detail_map[userid] = item
            roster_fields = self.config.get_dimission_roster_fields()
            roster_map = self.client.list_roster_infos(userids, field_codes=roster_fields)
            for userid, roster_fields in roster_map.items():
                if not isinstance(roster_fields, dict):
                    continue
                info = detail_map.setdefault(userid, {"userid": userid})
                employee_info = {}
                base_employee_info = info.get("employeeInfo") or info.get("employee_info")
                if isinstance(base_employee_info, dict):
                    employee_info.update(base_employee_info)

                def _extract(code: str, *, prefer_label: bool = False) -> Any:
                    entry = roster_fields.get(code)
                    if not isinstance(entry, dict):
                        return entry
                    value = entry.get("value")
                    label = entry.get("label")
                    if prefer_label and label not in (None, ""):
                        return label
                    return value if value not in (None, "") else label

                def _extract_list(code: str) -> list[Any]:
                    entry = roster_fields.get(code)
                    if isinstance(entry, dict):
                        values = entry.get("values")
                        if isinstance(values, list):
                            return [v for v in values if v not in (None, "")]
                    return []

                def _setdefault(target: dict[str, Any], key: str, value: Any) -> None:
                    if value in (None, "", [], {}):
                        return
                    current = target.get(key)
                    if current in (None, "", [], {}):
                        target[key] = value

                name_value = _extract("sys00-name", prefer_label=True)
                mobile_value = _extract("sys00-mobile")
                job_number_value = _extract("sys00-jobNumber") or _extract("sys00-employeeId")
                email_value = _extract("sys00-email") or _extract("sys00-orgEmail")
                position_value = _extract("sys00-position")
                main_dept_entry = roster_fields.get("sys00-mainDept")
                main_dept_id: Any = None
                main_dept_name: Any = None
                if isinstance(main_dept_entry, dict):
                    main_dept_id = main_dept_entry.get("value")
                    main_dept_name = main_dept_entry.get("label") or main_dept_entry.get("value")
                if main_dept_id in (None, ""):
                    main_dept_id = _extract("sys00-mainDeptId")

                dept_list_values = _extract_list("sys00-dept")

                for key, value in (
                    ("name", name_value),
                    ("mobile", mobile_value),
                    ("jobNumber", job_number_value),
                    ("job_number", job_number_value),
                    ("email", email_value),
                    ("title", position_value),
                    ("mainDeptId", main_dept_id),
                    ("main_dept_id", main_dept_id),
                    ("mainDeptName", main_dept_name),
                    ("main_dept_name", main_dept_name),
                ):
                    _setdefault(employee_info, key, value)
                    _setdefault(info, key, value)

                if dept_list_values:
                    existing_dept_ids = info.get("dept_ids") or info.get("deptIdList") or []
                    if not isinstance(existing_dept_ids, list):
                        existing_dept_ids = [existing_dept_ids]
                    combined = set()
                    for candidate in list(existing_dept_ids) + dept_list_values:
                        if candidate in (None, ""):
                            continue
                        combined.add(str(candidate))
                    if combined:
                        info["dept_ids"] = sorted(combined)
                if employee_info:
                    info["employeeInfo"] = employee_info
            record_map: dict[str, dict[str, Any]] = {}
            dimission_record_error: str | None = None
            if userids:
                try:
                    records = self.client.list_dimission_records()
                except DingTalkAPIError as exc:
                    dimission_record_error = str(exc)
                    logger.warning(
                        "获取离职人员离职记录失败 config=%s error=%s",
                        self.config.id,
                        dimission_record_error,
                    )
                    records = []
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    userid = str(record.get("userId") or record.get("userid") or "")
                    if userid and userid not in record_map:
                        record_map[userid] = record
            synced_ids: set[str] = set()
            now = timezone.now()
            with transaction.atomic():
                for userid in userids:
                    if not userid:
                        continue
                    info = detail_map.get(userid, {"userid": userid})
                    leave_record = record_map.get(userid)
                    defaults = map_dimission(self.config.id, info, leave_record)
                    defaults.setdefault("userid", userid)
                    defaults.pop("config_id", None)
                    DingTalkDimissionUser.objects.update_or_create(
                        config=self.config,
                        userid=userid,
                        defaults=defaults,
                    )
                    synced_ids.add(userid)
            stale_queryset = DingTalkDimissionUser.objects.filter(config=self.config).exclude(userid__in=synced_ids)
            stale_count = stale_queryset.count()
            if stale_count:
                stale_queryset.delete()

            stats = {"dimission_count": len(synced_ids), "stale_count": stale_count, "mode": mode}
            if dimission_record_error:
                stats["dimission_record_error"] = dimission_record_error
            message = f"同步离职人员完成 ({len(synced_ids)} 个)"
            self._record_log(
                SyncOperation.SYNC_DIMISSION_USERS,
                SyncStatus.SUCCESS,
                message=message,
                stats=stats,
            )
            self._update_sync_state(
                status=SyncStatus.SUCCESS,
                message=message,
                stats=stats,
                dimission_sync_time=now,
            )
            post_sync.send(
                sender=self.__class__,
                config=self.config,
                operation=SyncOperation.SYNC_DIMISSION_USERS.value,
                stats=stats,
            )
            return {"count": len(synced_ids), "staleCount": stale_count}
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(SyncOperation.SYNC_DIMISSION_USERS, exc)
            raise

    def sync_attendance(
        self,
        start_time: datetime,
        end_time: datetime,
        *,
        mode: str = "full",
        user_ids: Iterable[str] | None = None,
    ) -> dict:
        if start_time > end_time:
            raise DingTalkAPIError("开始时间不能晚于结束时间")

        explicit_userids: list[str] | None = None
        if user_ids is not None:
            explicit_userids = [uid for uid in dict.fromkeys(str(u).strip() for u in user_ids if u)]
            if not explicit_userids:
                return {"count": 0}
        else:
            self.ensure_enabled()

        pre_sync.send(sender=self.__class__, config=self.config, operation=SyncOperation.SYNC_ATTENDANCE.value)
        try:
            if explicit_userids is not None:
                userids = explicit_userids
            else:
                userids = list(
                    DingTalkUser.objects.filter(config=self.config).values_list("userid", flat=True)
                )
                if not userids:
                    self.sync_users()
                    userids = list(
                        DingTalkUser.objects.filter(config=self.config).values_list("userid", flat=True)
                    )
            if not userids:
                return {"count": 0}
            records = self.client.list_attendance_records(userids, start_time=start_time, end_time=end_time)
            synced_ids: set[str] = set()
            with transaction.atomic():
                for record in records:
                    defaults = map_attendance(self.config.id, record)
                    record_id = defaults.get("record_id")
                    if not record_id:
                        continue
                    DingTalkAttendanceRecord.objects.update_or_create(record_id=record_id, defaults=defaults)
                    synced_ids.add(record_id)
            stats = {
                "attendance_count": len(synced_ids),
                "mode": mode,
                "userIds": userids,
                "manual": explicit_userids is not None,
            }
            message = f"同步考勤完成 ({len(synced_ids)} 条)"
            self._record_log(
                SyncOperation.SYNC_ATTENDANCE,
                SyncStatus.SUCCESS,
                message=message,
                stats=stats,
            )
            self._update_sync_state(
                status=SyncStatus.SUCCESS,
                message=message,
                stats=stats,
                attendance_sync_time=end_time,
            )
            post_sync.send(
                sender=self.__class__,
                config=self.config,
                operation=SyncOperation.SYNC_ATTENDANCE.value,
                stats=stats,
            )
            return {"count": len(synced_ids)}
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(SyncOperation.SYNC_ATTENDANCE, exc)
            raise

    def preview_attendance(
        self,
        start_time: datetime,
        end_time: datetime,
        *,
        user_ids: Iterable[str] | None = None,
        limit: int | None = 200,
    ) -> list[dict]:
        if start_time > end_time:
            raise DingTalkAPIError("开始时间不能晚于结束时间")

        explicit_userids: list[str] | None = None
        if user_ids is not None:
            explicit_userids = [uid for uid in dict.fromkeys(str(u).strip() for u in user_ids if u)]
            if not explicit_userids:
                return []
        else:
            self.ensure_enabled()

        if explicit_userids is not None:
            userids = explicit_userids
        else:
            userids = list(DingTalkUser.objects.filter(config=self.config).values_list("userid", flat=True))
            if not userids:
                self.sync_users()
                userids = list(DingTalkUser.objects.filter(config=self.config).values_list("userid", flat=True))
        if not userids:
            return []

        records = self.client.list_attendance_records(userids, start_time=start_time, end_time=end_time)
        if limit is not None and limit > 0:
            records = records[:limit]
        mapped_records = [map_attendance(self.config.id, record) for record in records]
        serializer = DingTalkAttendancePreviewSerializer(mapped_records, many=True)
        return serializer.data

    def full_sync(self) -> dict:
        pre_sync.send(sender=self.__class__, config=self.config, operation=SyncOperation.FULL_SYNC.value)
        try:
            dept_result = self.sync_departments()
            user_result = self.sync_users()
            stats = {"dept_count": dept_result.get("count", 0), "user_count": user_result.get("count", 0)}
            message = f"全量同步完成，部门 {stats['dept_count']} 个，用户 {stats['user_count']} 个"
            self._record_log(
                SyncOperation.FULL_SYNC,
                SyncStatus.SUCCESS,
                message=message,
                stats=stats,
            )
            self._update_sync_state(status=SyncStatus.SUCCESS, message=message, stats=stats)
            post_sync.send(
                sender=self.__class__,
                config=self.config,
                operation=SyncOperation.FULL_SYNC.value,
                stats=stats,
            )
            return stats
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(SyncOperation.FULL_SYNC, exc)
            raise

    # --------------------------- 游标管理 --------------------------- #
    def get_cursor(self, cursor_type: str) -> SyncCursor:
        cursor, _ = SyncCursor.objects.get_or_create(config=self.config, cursor_type=cursor_type)
        return cursor

    def update_cursor(self, cursor_type: str, value: str, extra: dict | None = None) -> None:
        cursor = self.get_cursor(cursor_type)
        cursor.value = value
        if extra is not None:
            cursor.extra = extra
        cursor.save(update_fields=["value", "extra", "update_time"])


__all__ = ["SyncService"]
