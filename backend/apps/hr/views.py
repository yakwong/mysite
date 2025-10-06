from __future__ import annotations

from dataclasses import asdict
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action

from utils.response import CustomResponse
from utils.viewset import CustomModelViewSet

from .filters import AttendanceSummaryFilter, DepartmentFilter, EmployeeFilter, PayrollRecordFilter
from .models import AttendanceRule, AttendanceSummary, Department, Employee, PayrollRecord, PayrollRule
from .serializers import (
    AttendanceConfirmSerializer,
    AttendanceGenerateSerializer,
    AttendanceRuleSerializer,
    AttendanceSummarySerializer,
    DepartmentSerializer,
    EmployeeSerializer,
    PayrollGenerateSerializer,
    PayrollRecordSerializer,
    PayrollRuleSerializer,
)
from .services import AttendanceCalculator, DepartmentImporter, EmployeeImporter, PayrollCalculator


class DepartmentViewSet(CustomModelViewSet):
    queryset = (
        Department.objects.select_related("manager", "parent", "ding_department")
        .all()
        .order_by("code")
    )
    serializer_class = DepartmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DepartmentFilter

    @action(methods=["post"], detail=False, url_path="import/dingtalk")
    def import_from_dingtalk(self, request):
        config_id = request.data.get("configId")
        importer = DepartmentImporter(config_id=config_id)
        result = importer.sync()
        return CustomResponse(success=True, data=asdict(result), msg="导入钉钉部门完成")


class EmployeeViewSet(CustomModelViewSet):
    queryset = (
        Employee.objects.select_related("department", "user", "ding_user")
        .all()
        .order_by("job_number")
    )
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeFilter

    @action(methods=["post"], detail=False, url_path="import/dingtalk")
    def import_from_dingtalk(self, request):
        config_id = request.data.get("configId")
        if not Department.objects.filter(ding_department__isnull=False).exists():
            DepartmentImporter(config_id=config_id).sync()
        importer = EmployeeImporter(config_id=config_id)
        result = importer.sync()
        return CustomResponse(success=True, data=asdict(result), msg="导入钉钉员工完成")


class AttendanceRuleViewSet(CustomModelViewSet):
    queryset = AttendanceRule.objects.all().order_by("name")
    serializer_class = AttendanceRuleSerializer


class AttendanceSummaryViewSet(CustomModelViewSet):
    queryset = AttendanceSummary.objects.select_related("employee", "employee__department", "rule").all()
    serializer_class = AttendanceSummarySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttendanceSummaryFilter

    @action(methods=["post"], detail=False, url_path="calculate")
    def calculate(self, request):
        serializer = AttendanceGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rule = get_object_or_404(AttendanceRule, pk=data["rule_id"])
        employees = list(
            Employee.objects.select_related("ding_user")
            .filter(id__in=data["employeeIds"])
            .order_by("job_number")
        )
        if not employees:
            return CustomResponse(success=False, data=None, msg="未找到员工")
        calculator = AttendanceCalculator(rule)
        summaries = []
        for employee in employees:
            summary = calculator.calculate(employee, start=data["start"], end=data["end"])
            summaries.append(AttendanceSummarySerializer(summary).data)
        return CustomResponse(success=True, data=summaries, msg="考勤统计完成")

    @action(methods=["post"], detail=False, url_path="status")
    def bulk_status(self, request):
        serializer = AttendanceConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        status_value = serializer.validated_data["status"]
        updated = AttendanceSummary.objects.filter(id__in=ids).update(status=status_value)
        return CustomResponse(success=True, data={"updated": updated}, msg="状态更新完成")


class PayrollRuleViewSet(CustomModelViewSet):
    queryset = PayrollRule.objects.all().order_by("name")
    serializer_class = PayrollRuleSerializer


class PayrollRecordViewSet(CustomModelViewSet):
    queryset = (
        PayrollRecord.objects.select_related(
            "employee",
            "employee__department",
            "rule",
            "attendance_summary",
        )
        .all()
        .order_by("-period_start")
    )
    serializer_class = PayrollRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PayrollRecordFilter

    @action(methods=["post"], detail=False, url_path="calculate")
    def calculate(self, request):
        serializer = PayrollGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rule = get_object_or_404(PayrollRule, pk=data["rule_id"])
        employees = list(
            Employee.objects.select_related("department").filter(id__in=data["employeeIds"]).order_by("job_number")
        )
        if not employees:
            return CustomResponse(success=False, data=None, msg="未找到员工")
        summaries = AttendanceSummary.objects.filter(
            employee_id__in=data["employeeIds"],
            period_start=data["period_start"],
            period_end=data["period_end"],
        )
        summary_map = {str(item.employee_id): item for item in summaries}
        calculator = PayrollCalculator(rule)
        records = []
        missing: list[dict[str, str]] = []
        for employee in employees:
            summary = summary_map.get(str(employee.id))
            if not summary:
                missing.append({"employeeId": str(employee.id), "name": employee.name})
                continue
            record = calculator.calculate(employee, summary=summary)
            records.append(PayrollRecordSerializer(record).data)
        data = {"records": records, "missing": missing}
        msg = "薪资计算完成"
        if missing:
            msg += "，部分员工缺少考勤统计"
        return CustomResponse(success=bool(records), data=data, msg=msg)
