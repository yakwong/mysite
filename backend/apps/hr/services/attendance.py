from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Iterable

from django.utils import timezone

from apps.dingtalk.models import DingTalkAttendanceRecord

from ..models import AttendanceRule, AttendanceSummary, Employee


@dataclass(slots=True)
class AttendanceMetrics:
    work_days: int = 0
    present_days: int = 0
    late_minutes: int = 0
    early_leave_minutes: int = 0
    absence_days: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    detail: dict[str, dict[str, object]] = field(default_factory=dict)


class AttendanceCalculator:
    """根据钉钉打卡记录生成考勤统计"""

    def __init__(self, rule: AttendanceRule) -> None:
        self.rule = rule

    def calculate(self, employee: Employee, start: date, end: date) -> AttendanceSummary:
        metrics = self._aggregate(employee, start, end)
        summary, _ = AttendanceSummary.objects.update_or_create(
            employee=employee,
            period_start=start,
            period_end=end,
            defaults={
                "rule": self.rule,
                "work_days": metrics.work_days,
                "present_days": metrics.present_days,
                "late_minutes": metrics.late_minutes,
                "early_leave_minutes": metrics.early_leave_minutes,
                "absence_days": metrics.absence_days,
                "overtime_hours": metrics.overtime_hours,
                "detail": metrics.detail,
            },
        )
        return summary

    def _aggregate(self, employee: Employee, start: date, end: date) -> AttendanceMetrics:
        records = self._fetch_records(employee, start, end)
        buckets: dict[date, list[DingTalkAttendanceRecord]] = defaultdict(list)
        for record in records:
            if record.work_date:
                buckets[record.work_date].append(record)
        metrics = AttendanceMetrics()
        workdays = self._workdays(start, end)
        metrics.work_days = len(workdays)
        for workday in workdays:
            day_records = sorted(buckets.get(workday, []), key=lambda item: item.user_check_time)
            day_key = workday.isoformat()
            if not day_records:
                metrics.absence_days += Decimal("1")
                metrics.detail[day_key] = {
                    "status": "absent",
                    "records": [],
                }
                continue
            metrics.present_days += 1
            first = day_records[0]
            last = day_records[-1]
            late = self._late_minutes(first.user_check_time)
            early = self._early_minutes(last.user_check_time)
            overtime = self._overtime_hours(last.user_check_time)
            metrics.late_minutes += late
            metrics.early_leave_minutes += early
            metrics.overtime_hours += overtime
            status = "present"
            if late > self.rule.absence_minutes or early > self.rule.absence_minutes:
                metrics.absence_days += Decimal("1")
                status = "absence"
            metrics.detail[day_key] = {
                "status": status,
                "lateMinutes": late,
                "earlyLeaveMinutes": early,
                "overtimeHours": float(overtime),
                "records": [
                    {
                        "id": record.record_id,
                        "type": record.check_type,
                        "result": record.time_result,
                        "checkedAt": record.user_check_time.isoformat(),
                        "source": record.source_type,
                    }
                    for record in day_records
                ],
            }
        return metrics

    def _fetch_records(self, employee: Employee, start: date, end: date) -> Iterable[DingTalkAttendanceRecord]:
        if not employee.ding_user:
            return []
        qs = DingTalkAttendanceRecord.objects.filter(
            userid=employee.ding_user.userid,
            work_date__range=(start, end),
        ).order_by("user_check_time")
        return list(qs)

    def _workdays(self, start: date, end: date) -> list[date]:
        current = start
        dates: list[date] = []
        custom_days = set(self.rule.custom_workdays or [])
        while current <= end:
            weekday = current.isoweekday()
            if self.rule.weekend_as_workday or weekday in (custom_days or {1, 2, 3, 4, 5}):
                dates.append(current)
            elif weekday <= 5:
                dates.append(current)
            current = current + timedelta(days=1)
        return dates

    def _late_minutes(self, check_time: datetime) -> int:
        start_time = self._combine_time(check_time.date(), self.rule.workday_start)
        delta = (check_time - start_time).total_seconds() // 60
        if delta <= 0:
            return 0
        if delta <= self.rule.allow_late_minutes:
            return 0
        return int(delta - self.rule.allow_late_minutes)

    def _early_minutes(self, check_time: datetime) -> int:
        end_time = self._combine_time(check_time.date(), self.rule.workday_end)
        delta = (end_time - check_time).total_seconds() // 60
        if delta <= 0:
            return 0
        if delta <= self.rule.allow_early_minutes:
            return 0
        return int(delta - self.rule.allow_early_minutes)

    def _overtime_hours(self, check_time: datetime) -> Decimal:
        end_time = self._combine_time(check_time.date(), self.rule.workday_end)
        delta_minutes = (check_time - end_time).total_seconds() // 60
        if delta_minutes <= self.rule.overtime_start_minutes:
            return Decimal("0")
        return Decimal(delta_minutes - self.rule.overtime_start_minutes) / Decimal("60")

    @staticmethod
    def _combine_time(day: date, at: time) -> datetime:
        naive = datetime.combine(day, at)
        if timezone.is_naive(naive):
            return timezone.make_aware(naive, timezone.get_current_timezone())
        return naive
