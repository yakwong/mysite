from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import (
    AttendanceRule,
    AttendanceSummary,
    Department,
    Employee,
    PayrollRecord,
    PayrollRule,
)


class DepartmentSerializer(serializers.ModelSerializer):
    managerName = serializers.CharField(source="manager.username", read_only=True)
    parentName = serializers.CharField(source="parent.name", read_only=True)
    dingDeptId = serializers.CharField(source="ding_department.dept_id", read_only=True)

    statusLabel = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "config_id",
            "status",
            "statusLabel",
            "description",
            "metadata",
            "parent",
            "parentName",
            "manager",
            "managerName",
            "ding_department",
            "dingDeptId",
            "create_time",
            "update_time",
        ]
        read_only_fields = ["create_time", "update_time"]


class EmployeeSerializer(serializers.ModelSerializer):
    departmentName = serializers.CharField(source="department.name", read_only=True)
    employmentStatusLabel = serializers.CharField(source="get_employment_status_display", read_only=True)
    employmentTypeLabel = serializers.CharField(source="get_employment_type_display", read_only=True)
    dingUserId = serializers.CharField(source="ding_user.userid", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "job_number",
            "config_id",
            "email",
            "phone",
            "title",
            "employment_type",
            "employmentTypeLabel",
            "employment_status",
            "employmentStatusLabel",
            "hire_date",
            "regular_date",
            "separation_date",
            "base_salary",
            "allowance",
            "metadata",
            "department",
            "departmentName",
            "user",
            "ding_user",
            "dingUserId",
            "create_time",
            "update_time",
        ]
        read_only_fields = ["create_time", "update_time"]


class AttendanceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRule
        fields = [
            "id",
            "name",
            "description",
            "workday_start",
            "workday_end",
            "allow_late_minutes",
            "allow_early_minutes",
            "absence_minutes",
            "overtime_start_minutes",
            "weekend_as_workday",
            "custom_workdays",
            "create_time",
            "update_time",
        ]
        read_only_fields = ["create_time", "update_time"]


class AttendanceSummarySerializer(serializers.ModelSerializer):
    employeeName = serializers.CharField(source="employee.name", read_only=True)
    employeeJobNumber = serializers.CharField(source="employee.job_number", read_only=True)
    ruleName = serializers.CharField(source="rule.name", read_only=True)

    statusLabel = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AttendanceSummary
        fields = [
            "id",
            "employee",
            "employeeName",
            "employeeJobNumber",
            "rule",
            "ruleName",
            "period_start",
            "period_end",
            "work_days",
            "present_days",
            "late_minutes",
            "early_leave_minutes",
            "absence_days",
            "overtime_hours",
            "detail",
            "status",
            "statusLabel",
            "create_time",
            "update_time",
        ]
        read_only_fields = ["create_time", "update_time"]


class AttendanceGenerateSerializer(serializers.Serializer):
    ruleId = serializers.UUIDField(source="rule_id")
    employeeIds = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    start = serializers.DateField()
    end = serializers.DateField()

    def validate(self, attrs: dict) -> dict:
        start = attrs["start"]
        end = attrs["end"]
        if start > end:
            raise serializers.ValidationError("结束日期必须不早于开始日期")
        if (end - start).days > 62:
            raise serializers.ValidationError("统计周期不超过两个月")
        return attrs


class AttendanceConfirmSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    status = serializers.ChoiceField(choices=AttendanceSummary.Status.choices)


class PayrollRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRule
        fields = [
            "id",
            "name",
            "description",
            "overtime_rate",
            "late_penalty_per_minute",
            "absence_penalty_per_day",
            "tax_rate",
            "other_allowance",
            "create_time",
            "update_time",
        ]
        read_only_fields = ["create_time", "update_time"]


class PayrollRecordSerializer(serializers.ModelSerializer):
    employeeName = serializers.CharField(source="employee.name", read_only=True)
    employeeJobNumber = serializers.CharField(source="employee.job_number", read_only=True)
    ruleName = serializers.CharField(source="rule.name", read_only=True)

    statusLabel = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PayrollRecord
        fields = [
            "id",
            "employee",
            "employeeName",
            "employeeJobNumber",
            "rule",
            "ruleName",
            "attendance_summary",
            "period_start",
            "period_end",
            "gross_salary",
            "deductions",
            "tax",
            "net_salary",
            "detail",
            "remark",
            "status",
            "statusLabel",
            "paid_at",
            "create_time",
            "update_time",
        ]
        read_only_fields = ["create_time", "update_time"]


class PayrollGenerateSerializer(serializers.Serializer):
    ruleId = serializers.UUIDField(source="rule_id")
    employeeIds = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    periodStart = serializers.DateField(source="period_start")
    periodEnd = serializers.DateField(source="period_end")

    def validate(self, attrs: dict) -> dict:
        start = attrs["period_start"]
        end = attrs["period_end"]
        if start > end:
            raise serializers.ValidationError("发薪结束日期必须不早于开始日期")
        now = timezone.now().date()
        if end > now + timedelta(days=7):
            raise serializers.ValidationError("发薪周期不能超过当前日期一周")
        return attrs
