from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
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


__all__ = [
    "map_department",
    "map_user",
    "map_attendance",
]
