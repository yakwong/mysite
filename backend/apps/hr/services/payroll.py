from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.db import transaction

from ..models import AttendanceSummary, Employee, PayrollRecord, PayrollRule


@dataclass(slots=True)
class PayrollBreakdown:
    base_salary: Decimal
    allowance: Decimal
    overtime: Decimal
    penalties: Decimal
    taxable: Decimal
    tax: Decimal
    net: Decimal


class PayrollCalculator:
    """根据考勤统计和规则计算薪资"""

    def __init__(self, rule: PayrollRule) -> None:
        self.rule = rule

    @transaction.atomic
    def calculate(
        self,
        employee: Employee,
        *,
        summary: AttendanceSummary | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        status: PayrollRecord.Status = PayrollRecord.Status.DRAFT,
    ) -> PayrollRecord:
        if summary is None:
            if period_start is None or period_end is None:
                raise ValueError("缺少考勤统计或期间")
            summary = AttendanceSummary.objects.get(
                employee=employee,
                period_start=period_start,
                period_end=period_end,
            )
        else:
            period_start = summary.period_start
            period_end = summary.period_end
        breakdown = self._breakdown(employee, summary)
        record, _ = PayrollRecord.objects.update_or_create(
            employee=employee,
            period_start=period_start,
            period_end=period_end,
            defaults={
                "rule": self.rule,
                "attendance_summary": summary,
                "gross_salary": (breakdown.base_salary + breakdown.allowance + breakdown.overtime).quantize(Decimal("0.01")),
                "deductions": breakdown.penalties.quantize(Decimal("0.01")),
                "net_salary": breakdown.net,
                "tax": breakdown.tax,
                "detail": {
                    "base": str(breakdown.base_salary),
                    "allowance": str(breakdown.allowance),
                    "overtime": str(breakdown.overtime),
                    "penalties": str(breakdown.penalties),
                    "taxable": str(breakdown.taxable),
                },
                "status": status,
            },
        )
        return record

    def bulk_calculate(
        self,
        employees: Iterable[Employee],
        *,
        period_start: date,
        period_end: date,
        summaries: dict[str, AttendanceSummary] | None = None,
    ) -> list[PayrollRecord]:
        results: list[PayrollRecord] = []
        for employee in employees:
            summary = None
            if summaries is not None:
                summary = summaries.get(str(employee.id))
            record = self.calculate(
                employee,
                summary=summary,
                period_start=period_start,
                period_end=period_end,
            )
            results.append(record)
        return results

    def _breakdown(self, employee: Employee, summary: AttendanceSummary) -> PayrollBreakdown:
        base_salary = Decimal(employee.base_salary)
        allowance = Decimal(employee.allowance) + Decimal(self.rule.other_allowance)
        hourly_rate = self._hourly_rate(base_salary, summary.work_days)
        overtime = (hourly_rate * Decimal(summary.overtime_hours) * Decimal(self.rule.overtime_rate)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        penalties = (
            Decimal(self.rule.late_penalty_per_minute) * Decimal(summary.late_minutes)
            + Decimal(self.rule.absence_penalty_per_day) * Decimal(summary.absence_days)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross = base_salary + allowance + overtime
        taxable = (gross - penalties).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax = (taxable * Decimal(self.rule.tax_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net = (taxable - tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return PayrollBreakdown(
            base_salary=base_salary.quantize(Decimal("0.01")),
            allowance=allowance.quantize(Decimal("0.01")),
            overtime=overtime,
            penalties=penalties,
            taxable=taxable,
            tax=tax,
            net=net,
        )

    @staticmethod
    def _hourly_rate(base_salary: Decimal, work_days: int) -> Decimal:
        if work_days <= 0:
            work_days = 21
        hours = Decimal(work_days * 8)
        if hours <= 0:
            hours = Decimal("168")
        return (base_salary / hours).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
