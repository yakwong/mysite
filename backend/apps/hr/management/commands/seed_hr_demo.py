from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.hr.models import (
    AttendanceRule,
    AttendanceSummary,
    Department,
    Employee,
    PayrollRecord,
    PayrollRule,
)
from apps.user.models import User


class Command(BaseCommand):
    help = "Seed demo data for the HR module (departments, employees, attendance, payroll)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset previously generated demo data before seeding again.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            PayrollRecord.objects.all().delete()
            AttendanceSummary.objects.all().delete()
            Employee.objects.all().delete()
            Department.objects.all().delete()
            AttendanceRule.objects.all().delete()
            PayrollRule.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing HR demo data."))

        admin = User.objects.filter(username="admin").first()

        hq, _ = Department.objects.get_or_create(
            code="HQ",
            defaults={
                "name": "总部",
                "manager": admin,
                "description": "集团总部",
            },
        )
        dev, _ = Department.objects.get_or_create(
            code="DEV",
            defaults={
                "name": "研发中心",
                "parent": hq,
                "manager": admin,
                "description": "产品与平台研发团队",
            },
        )

        employee, _ = Employee.objects.get_or_create(
            job_number="E1001",
            defaults={
                "name": "张三",
                "department": dev,
                "email": "zhangsan@example.com",
                "phone": "13800000000",
                "title": "后端工程师",
                "employment_type": Employee.EmploymentType.FULL_TIME,
                "employment_status": Employee.EmploymentStatus.FULL_TIME,
                "hire_date": date(2023, 1, 3),
                "regular_date": date(2023, 4, 3),
                "base_salary": Decimal("18000.00"),
                "allowance": Decimal("1000.00"),
            },
        )

        rule, _ = AttendanceRule.objects.get_or_create(
            name="标准工时",
            defaults={
                "description": "9:00-18:00 标准工时",
                "workday_start": time(9, 0),
                "workday_end": time(18, 0),
                "allow_late_minutes": 5,
                "allow_early_minutes": 5,
                "absence_minutes": 60,
                "overtime_start_minutes": 30,
                "weekend_as_workday": False,
                "custom_workdays": [1, 2, 3, 4, 5],
            },
        )

        summary, _ = AttendanceSummary.objects.get_or_create(
            employee=employee,
            rule=rule,
            period_start=date(2025, 9, 30),
            period_end=date(2025, 10, 6),
            defaults={
                "work_days": 5,
                "present_days": 5,
                "late_minutes": 0,
                "early_leave_minutes": 0,
                "absence_days": Decimal("0.00"),
                "overtime_hours": Decimal("2.50"),
                "detail": {
                    "2025-10-02": {
                        "status": "overtime",
                        "overtimeHours": 2.5,
                        "records": [],
                    }
                },
                "status": AttendanceSummary.Status.CONFIRMED,
            },
        )

        payroll_rule, _ = PayrollRule.objects.get_or_create(
            name="默认薪资规则",
            defaults={
                "description": "基本薪资 + 加班费",
                "overtime_rate": Decimal("1.5"),
                "late_penalty_per_minute": Decimal("10"),
                "absence_penalty_per_day": Decimal("500"),
                "tax_rate": Decimal("0.1"),
                "other_allowance": Decimal("500"),
            },
        )

        PayrollRecord.objects.get_or_create(
            employee=employee,
            rule=payroll_rule,
            period_start=date(2025, 9, 30),
            period_end=date(2025, 10, 6),
            defaults={
                "attendance_summary": summary,
                "gross_salary": Decimal("5000.00"),
                "deductions": Decimal("200.00"),
                "net_salary": Decimal("4800.00"),
                "tax": Decimal("500.00"),
                "remark": "10月第一周",
                "detail": {"period": "2025-09-30~2025-10-06"},
                "status": PayrollRecord.Status.APPROVED,
            },
        )

        self.stdout.write(self.style.SUCCESS("HR demo data synced."))
