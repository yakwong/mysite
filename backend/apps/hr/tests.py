from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.dingtalk.models import DingTalkAttendanceRecord, DingTalkConfig, DingTalkDepartment, DingTalkUser

from .models import AttendanceRule, AttendanceSummary, Department, Employee, PayrollRule
from .services import AttendanceCalculator, DepartmentImporter, EmployeeImporter, PayrollCalculator


class HrImporterTests(TestCase):
    def setUp(self) -> None:
        self.config = DingTalkConfig.objects.create(id="default", name="默认配置")

    def test_department_importer_sync(self) -> None:
        DingTalkDepartment.objects.create(
            dept_id=1001,
            config=self.config,
            name="研发部",
            parent_id=None,
            order=1,
            leader_userid="manager1",
            source_info={"brief": "技术研发"},
        )
        importer = DepartmentImporter(config_id=self.config.id)
        result = importer.sync()
        self.assertEqual(result.created, 1)
        self.assertEqual(Department.objects.count(), 1)
        dept = Department.objects.get()
        self.assertEqual(dept.name, "研发部")
        self.assertEqual(dept.metadata.get("brief"), "技术研发")

    def test_employee_importer_sync(self) -> None:
        ding_dept = DingTalkDepartment.objects.create(
            dept_id=2001,
            config=self.config,
            name="人事部",
            parent_id=None,
            order=1,
        )
        DepartmentImporter(config_id=self.config.id).sync()
        DingTalkUser.objects.create(
            userid="user123",
            config=self.config,
            name="张三",
            job_number="E0001",
            mobile="13800001111",
            email="zhangsan@example.com",
            dept_ids=[ding_dept.dept_id],
            source_info={"title": "HR"},
        )
        importer = EmployeeImporter(config_id=self.config.id)
        result = importer.sync()
        self.assertEqual(result.created, 1)
        employee = Employee.objects.get()
        self.assertEqual(employee.name, "张三")
        self.assertEqual(employee.department.name, "人事部")
        self.assertEqual(employee.metadata.get("title"), "HR")


class AttendanceCalculatorTests(TestCase):
    def setUp(self) -> None:
        self.config = DingTalkConfig.objects.create(id="default", name="默认配置")
        self.ding_dept = DingTalkDepartment.objects.create(
            dept_id=3001,
            config=self.config,
            name="平台组",
        )
        DepartmentImporter(config_id=self.config.id).sync()
        self.department = Department.objects.get()
        self.ding_user = DingTalkUser.objects.create(
            userid="u001",
            config=self.config,
            name="李四",
            job_number="DEV001",
            dept_ids=[self.ding_dept.dept_id],
        )
        self.employee = Employee.objects.create(
            name="李四",
            job_number="DEV001",
            department=self.department,
            ding_user=self.ding_user,
            base_salary=Decimal("10000"),
            allowance=Decimal("500"),
        )
        self.rule = AttendanceRule.objects.create(
            name="标准班制",
            workday_start=time(hour=9, minute=0),
            workday_end=time(hour=18, minute=0),
            allow_late_minutes=5,
            allow_early_minutes=5,
            absence_minutes=120,
            overtime_start_minutes=30,
        )

    def test_calculate_summary(self) -> None:
        # 第一天：9:10 打卡上班，18:40 下班
        work_day = date(2025, 9, 1)
        tz = timezone.get_current_timezone()
        DingTalkAttendanceRecord.objects.create(
            record_id="rec1",
            config=self.config,
            userid=self.ding_user.userid,
            check_type="OnDuty",
            time_result="Normal",
            user_check_time=timezone.make_aware(datetime.combine(work_day, time(9, 10)), tz),
            work_date=work_day,
        )
        DingTalkAttendanceRecord.objects.create(
            record_id="rec2",
            config=self.config,
            userid=self.ding_user.userid,
            check_type="OffDuty",
            time_result="Normal",
            user_check_time=timezone.make_aware(datetime.combine(work_day, time(18, 40)), tz),
            work_date=work_day,
        )
        calculator = AttendanceCalculator(self.rule)
        summary = calculator.calculate(self.employee, start=work_day, end=date(2025, 9, 2))
        self.assertEqual(summary.work_days, 2)
        self.assertEqual(summary.present_days, 1)
        self.assertEqual(summary.late_minutes, 5)  # 允许5分钟，超出为5
        self.assertAlmostEqual(float(summary.overtime_hours), 0.17, places=2)
        self.assertEqual(summary.absence_days, Decimal("1"))
        self.assertIn(work_day.isoformat(), summary.detail)


class PayrollCalculatorTests(TestCase):
    def setUp(self) -> None:
        self.config = DingTalkConfig.objects.create(id="default", name="默认配置")
        self.department = Department.objects.create(name="薪资组", code="FIN001")
        self.employee = Employee.objects.create(
            name="王五",
            job_number="FIN001",
            department=self.department,
            base_salary=Decimal("12000"),
            allowance=Decimal("800"),
        )
        self.rule = PayrollRule.objects.create(
            name="标准薪资",
            overtime_rate=Decimal("1.5"),
            late_penalty_per_minute=Decimal("20"),
            absence_penalty_per_day=Decimal("300"),
            tax_rate=Decimal("0.1"),
            other_allowance=Decimal("200"),
        )
        self.summary = AttendanceSummary.objects.create(
            employee=self.employee,
            rule=AttendanceRule.objects.create(
                name="班制",
                workday_start=time(9, 0),
                workday_end=time(18, 0),
                allow_late_minutes=10,
                allow_early_minutes=10,
                absence_minutes=120,
                overtime_start_minutes=30,
            ),
            period_start=date(2025, 9, 1),
            period_end=date(2025, 9, 30),
            work_days=22,
            present_days=21,
            late_minutes=30,
            early_leave_minutes=0,
            absence_days=Decimal("1"),
            overtime_hours=Decimal("6"),
        )

    def test_calculate_payroll_record(self) -> None:
        calculator = PayrollCalculator(self.rule)
        record = calculator.calculate(self.employee, summary=self.summary)
        self.assertEqual(record.rule, self.rule)
        self.assertEqual(record.employee, self.employee)
        self.assertGreater(record.net_salary, Decimal("0"))
        self.assertIn("base", record.detail)
