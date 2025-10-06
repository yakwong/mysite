from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.dingtalk.models import (
    DingTalkAttendanceRecord,
    DingTalkConfig,
    DingTalkDepartment,
    DingTalkUser,
)
from apps.hr.models import AttendanceSummary, Employee
from apps.user.models import User


class HrApiIntegrationTests(APITestCase):
    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminPass123",
        )
        self.client.force_authenticate(user=self.superuser)
        self.config = DingTalkConfig.objects.create(id="hr-test", name="联调配置", enabled=True)

    def _bootstrap_department_and_employee(self) -> Employee:
        DingTalkDepartment.objects.create(
            dept_id=9001,
            config=self.config,
            name="联合测试部",
            parent_id=None,
        )
        resp = self.client.post(
            "/api/hr/departments/import/dingtalk/",
            {"configId": self.config.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.data["data"]["created"], 1)

        DingTalkUser.objects.create(
            userid="u9001",
            config=self.config,
            name="测试员工",
            job_number="HR001",
            dept_ids=[9001],
            email="tester@example.com",
            mobile="13800000000",
        )
        resp = self.client.post(
            "/api/hr/employees/import/dingtalk/",
            {"configId": self.config.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        employee = Employee.objects.get(job_number="HR001")
        employee.base_salary = Decimal("12000")
        employee.allowance = Decimal("800")
        employee.save(update_fields=["base_salary", "allowance", "update_time"])
        return employee

    def test_full_hr_flow(self) -> None:
        employee = self._bootstrap_department_and_employee()

        rule_resp = self.client.post(
            "/api/hr/attendance/rules/",
            {
                "name": "联调考勤",
                "description": "集成测试规则",
                "workday_start": "09:00",
                "workday_end": "18:00",
                "allow_late_minutes": 10,
                "allow_early_minutes": 10,
                "absence_minutes": 120,
                "overtime_start_minutes": 30,
                "weekend_as_workday": False,
                "custom_workdays": [1, 2, 3, 4, 5],
            },
            format="json",
        )
        self.assertEqual(rule_resp.status_code, 201)
        attendance_rule_id = rule_resp.data["data"]["id"]

        today = date.today()
        check_in = timezone.make_aware(datetime.combine(today, time(hour=9, minute=5)))
        check_out = timezone.make_aware(datetime.combine(today, time(hour=19, minute=0)))
        DingTalkAttendanceRecord.objects.create(
            record_id="rec-9001",
            config=self.config,
            userid="u9001",
            check_type="OnDuty",
            time_result="Normal",
            user_check_time=check_in,
            work_date=today,
        )
        DingTalkAttendanceRecord.objects.create(
            record_id="rec-9001-out",
            config=self.config,
            userid="u9001",
            check_type="OffDuty",
            time_result="Normal",
            user_check_time=check_out,
            work_date=today,
        )

        summary_resp = self.client.post(
            "/api/hr/attendance/summary/calculate/",
            {
                "ruleId": attendance_rule_id,
                "employeeIds": [str(employee.id)],
                "start": today.isoformat(),
                "end": today.isoformat(),
            },
            format="json",
        )
        self.assertEqual(summary_resp.status_code, 200)
        self.assertTrue(summary_resp.data["success"])
        summary_id = summary_resp.data["data"][0]["id"]

        status_resp = self.client.post(
            "/api/hr/attendance/summary/status/",
            {"ids": [summary_id], "status": 2},
            format="json",
        )
        self.assertEqual(status_resp.status_code, 200)
        self.assertEqual(status_resp.data["data"]["updated"], 1)

        payroll_rule_resp = self.client.post(
            "/api/hr/payroll/rules/",
            {
                "name": "联调薪资",
                "description": "联调自动化",
                "overtime_rate": "1.5",
                "late_penalty_per_minute": "10",
                "absence_penalty_per_day": "300",
                "tax_rate": "0.1",
                "other_allowance": "200",
            },
            format="json",
        )
        self.assertEqual(payroll_rule_resp.status_code, 201)
        payroll_rule_id = payroll_rule_resp.data["data"]["id"]

        payroll_resp = self.client.post(
            "/api/hr/payroll/records/calculate/",
            {
                "ruleId": payroll_rule_id,
                "employeeIds": [str(employee.id)],
                "periodStart": today.isoformat(),
                "periodEnd": today.isoformat(),
            },
            format="json",
        )
        self.assertEqual(payroll_resp.status_code, 200)
        records = payroll_resp.data["data"]["records"]
        self.assertTrue(records)
        self.assertEqual(records[0]["employee"], str(employee.id))

        summary = AttendanceSummary.objects.get(id=summary_id)
        self.assertEqual(summary.status, 2)
