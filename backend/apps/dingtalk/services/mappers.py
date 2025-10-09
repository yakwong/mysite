from __future__ import annotations

from datetime import date, datetime, timezone as dt_timezone
from typing import Any, Dict

from django.utils import timezone

from ..models import DingTalkAttendanceRecord, DingTalkDepartment, DingTalkUser


def _parse_datetime(value: Any) -> timezone.datetime | None:
    if value in (None, ""):
        return None

    current_tz = timezone.get_current_timezone()

    if isinstance(value, datetime):
        if timezone.is_aware(value):
            return value.astimezone(current_tz)
        return timezone.make_aware(value, current_tz)

    if isinstance(value, (int, float)):
        timestamp = float(value)
        while timestamp > 1e12:
            timestamp /= 1000.0
        dt = datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)
        return dt.astimezone(current_tz)

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(current_tz)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    parsed = datetime.strptime(value, fmt)
                    return timezone.make_aware(parsed, current_tz)
                except ValueError:
                    continue
    return None


def _parse_date(value: Any) -> datetime.date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        try:
            timestamp = float(value)
        except (TypeError, ValueError):
            return None
        while timestamp > 1e12:
            timestamp /= 1000.0
        return datetime.fromtimestamp(timestamp, tz=dt_timezone.utc).date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value[:10], fmt).date()
            except ValueError:
                continue
    return None


def map_department(config_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "dept_id": payload.get("dept_id"),
        "config_id": config_id,
        "name": payload.get("name", ""),
        "parent_id": payload.get("parent_id"),
        "order": payload.get("order") or payload.get("dept_order"),
        "leader_userid": payload.get("leader_userid", ""),
        "dept_type": payload.get("dept_tag", ""),
        "source_info": payload,
    }


def map_user(config_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    dept_ids = payload.get("dept_id_list") or payload.get("deptIdList") or []
    return {
        "userid": payload.get("userid"),
        "config_id": config_id,
        "name": payload.get("name", ""),
        "mobile": payload.get("mobile", ""),
        "email": payload.get("email", ""),
        "active": payload.get("active", True),
        "job_number": payload.get("job_number", ""),
        "title": payload.get("title", ""),
        "dept_ids": sorted({int(item) for item in dept_ids if str(item).isdigit()}),
        "unionid": payload.get("unionid", ""),
        "remark": payload.get("remark", ""),
        "source_info": payload,
    }


def map_attendance(config_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    check_dt = _parse_datetime(payload.get("user_check_time") or payload.get("userCheckTime"))
    work_date_raw = payload.get("work_date") or payload.get("workDate")
    work_date = None
    if isinstance(work_date_raw, str):
        try:
            work_date = datetime.fromisoformat(work_date_raw).date()
        except ValueError:
            try:
                work_date = datetime.strptime(work_date_raw, "%Y-%m-%d").date()
            except ValueError:
                work_date = None
    elif isinstance(work_date_raw, datetime):
        work_date = work_date_raw.date()

    record_id = payload.get("record_id") or payload.get("recordId")
    if not record_id and check_dt:
        record_id = f"{payload.get('userid') or payload.get('userId')}_{int(check_dt.timestamp())}"

    return {
        "record_id": record_id,
        "config_id": config_id,
        "userid": payload.get("userid") or payload.get("userId"),
        "check_type": payload.get("check_type") or payload.get("checkType", ""),
        "time_result": payload.get("time_result") or payload.get("timeResult", ""),
        "user_check_time": check_dt or timezone.now(),
        "work_date": work_date,
        "source_type": payload.get("source_type") or payload.get("sourceType", ""),
        "source_info": payload,
    }


def map_dimission(config_id: str, info: Dict[str, Any], leave_record: Dict[str, Any] | None = None) -> Dict[str, Any]:
    leave_record = leave_record or {}
    sources: tuple[Dict[str, Any], ...] = tuple(
        item for item in (info, leave_record, info.get("employeeInfo"), info.get("employee_info")) if isinstance(item, dict)
    ) or ({},)

    def _extract(keys: tuple[str, ...], default: Any = "") -> Any:
        """从多个数据源中提取首个有效值，兼容大小写/下划线差异."""

        for source in sources:
            for key in keys:
                current: Any = source
                for part in key.split("."):
                    if not isinstance(current, dict):
                        current = None
                        break
                    current = current.get(part)
                if current in (None, "", [], {}):
                    continue
                if isinstance(current, str):
                    trimmed = current.strip()
                    if not trimmed:
                        continue
                    return trimmed
                return current
        return default

    def _extract_int(keys: tuple[str, ...]) -> int | None:
        value = _extract(keys, default=None)
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    last_work_day = _parse_date(
        _extract(
            (
                "last_work_day",
                "lastWorkDay",
                "last_workday",
                "lastWorkday",
                "lastWorkDate",
                "employeeInfo.lastWorkDay",
                "employee_info.lastWorkDay",
                "leaveRecord.lastWorkDay",
            ),
            default=None,
        )
    )
    leave_time = _parse_datetime(
        _extract(
            (
                "leave_time",
                "leaveTime",
                "leaveRecord.leaveTime",
                "leave_record.leaveTime",
                "leaveRecord.leave_time",
                "employeeInfo.leaveTime",
                "employee_info.leaveTime",
            ),
            default=None,
        )
    )
    dept_values_raw: list[Any] = []
    base_depts = info.get("dept_ids") or info.get("dept_ids_list") or info.get("deptIdList")
    if base_depts:
        if isinstance(base_depts, str):
            dept_values_raw.extend(item.strip() for item in base_depts.split(",") if item.strip())
        elif isinstance(base_depts, (list, tuple, set)):
            dept_values_raw.extend(base_depts)
        else:
            dept_values_raw.append(base_depts)
    dept_list = info.get("deptList") or leave_record.get("deptList") or []
    if isinstance(dept_list, list):
        for item in dept_list:
            if not isinstance(item, dict):
                continue
            candidate = item.get("dept_id") or item.get("deptId")
            if candidate is not None:
                dept_values_raw.append(candidate)
    dept_ids: list[int] = []
    for raw in dept_values_raw:
        try:
            dept_ids.append(int(raw))
        except (TypeError, ValueError):
            continue
    dept_ids = sorted(set(dept_ids))

    def _ensure_list(value: Any) -> list[Any]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return [value]

    voluntary_list = _ensure_list(
        _extract(
            (
                "voluntary_reason_set",
                "voluntaryReasons",
                "voluntary_reason_list",
                "voluntaryReasonList",
                "voluntaryReason",
                "leaveRecord.voluntaryReasons",
                "leaveRecord.voluntaryReason",
            ),
            default=[],
        )
    )
    passive_list = _ensure_list(
        _extract(
            (
                "passive_reason_set",
                "passiveReasons",
                "passive_reason_list",
                "passiveReasonList",
                "passiveReason",
                "leaveRecord.passiveReasons",
                "leaveRecord.passiveReason",
            ),
            default=[],
        )
    )
    leave_reason = _extract(
        (
            "leave_reason",
            "leaveReason",
            "leave_record.leaveReason",
            "leaveRecord.leaveReason",
            "leaveRecord.reason",
            "reason",
            "reasonMemo",
            "leaveRecord.reasonMemo",
        ),
        default="",
    )
    if not leave_reason:
        if voluntary_list:
            leave_reason = "、".join(str(item) for item in voluntary_list if item)
        elif passive_list:
            leave_reason = "、".join(str(item) for item in passive_list if item)

    return {
        "config_id": config_id,
        "userid": _extract(("userid", "userId"), default=""),
        "name": _extract(
            (
                "name",
                "userName",
                "employee_name",
                "employeeName",
                "staff_name",
                "staffName",
                "user_name",
                "realName",
                "employeeInfo.name",
                "employee_info.name",
                "leaveRecord.userName",
            ),
            default="",
        ),
        "mobile": _extract(
            (
                "mobile",
                "mobilePhone",
                "mobile_phone",
                "phone",
                "phoneNumber",
                "phone_number",
                "employeeInfo.mobile",
                "employee_info.mobile",
                "leaveRecord.mobile",
            ),
            default="",
        ),
        "job_number": _extract(
            (
                "job_number",
                "jobNumber",
                "job_no",
                "jobNo",
                "employeeCode",
                "employeeId",
                "leaveRecord.jobNumber",
            ),
            default="",
        ),
        "main_dept_id": _extract_int(
            (
                "main_dept_id",
                "mainDeptId",
                "main_department_id",
                "dept_id",
                "deptId",
                "employeeInfo.mainDeptId",
                "employee_info.mainDeptId",
                "leaveRecord.deptId",
            )
        ),
        "main_dept_name": _extract(
            (
                "main_dept_name",
                "mainDeptName",
                "main_department_name",
                "dept_name",
                "deptName",
                "employeeInfo.mainDeptName",
                "employee_info.mainDeptName",
                "leaveRecord.deptName",
            ),
            default="",
        ),
        "handover_userid": _extract(
            (
                "handover_userid",
                "handoverUserId",
                "handover_user_id",
                "handoverUserID",
                "leaveRecord.handoverUserId",
            ),
            default="",
        ),
        "last_work_day": last_work_day,
        "leave_time": leave_time,
        "leave_reason": leave_reason,
        "reason_type": _extract(("reason_type", "reasonType", "leaveRecord.reasonType"), default=None),
        "reason_memo": _extract(("reason_memo", "reasonMemo", "leaveRecord.reasonMemo"), default=""),
        "pre_status": _extract(("pre_status", "preStatus", "leaveRecord.preStatus"), default=None),
        "status": _extract(("status", "statusCode", "leaveRecord.status"), default=None),
        "voluntary_reasons": voluntary_list,
        "passive_reasons": passive_list,
        "dept_ids": dept_ids,
        "source_info": {**info, **({"leave_record": leave_record} if leave_record else {})},
    }


__all__ = [
    "map_department",
    "map_user",
    "map_attendance",
    "map_dimission",
]
