from __future__ import annotations

import django_filters

from .models import AttendanceSummary, Department, Employee, PayrollRecord


class DepartmentFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(method="filter_keyword")
    status = django_filters.NumberFilter(field_name="status")

    class Meta:
        model = Department
        fields = ["status", "config_id", "parent"]

    def filter_keyword(self, queryset, name, value):  # noqa: ARG002
        if not value:
            return queryset
        return queryset.filter(name__icontains=value) | queryset.filter(code__icontains=value)


class EmployeeFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(method="filter_keyword")
    department = django_filters.UUIDFilter(field_name="department_id")
    status = django_filters.NumberFilter(field_name="employment_status")
    configId = django_filters.CharFilter(field_name="config_id")

    class Meta:
        model = Employee
        fields = ["department", "employment_status", "employment_type", "config_id"]

    def filter_keyword(self, queryset, name, value):  # noqa: ARG002
        if not value:
            return queryset
        return queryset.filter(name__icontains=value) | queryset.filter(job_number__icontains=value)


class AttendanceSummaryFilter(django_filters.FilterSet):
    employee = django_filters.UUIDFilter(field_name="employee_id")
    rule = django_filters.UUIDFilter(field_name="rule_id")
    status = django_filters.NumberFilter(field_name="status")
    start = django_filters.DateFilter(field_name="period_start", lookup_expr="gte")
    end = django_filters.DateFilter(field_name="period_end", lookup_expr="lte")

    class Meta:
        model = AttendanceSummary
        fields = ["employee", "rule", "status"]


class PayrollRecordFilter(django_filters.FilterSet):
    employee = django_filters.UUIDFilter(field_name="employee_id")
    rule = django_filters.UUIDFilter(field_name="rule_id")
    status = django_filters.NumberFilter(field_name="status")
    start = django_filters.DateFilter(field_name="period_start", lookup_expr="gte")
    end = django_filters.DateFilter(field_name="period_end", lookup_expr="lte")

    class Meta:
        model = PayrollRecord
        fields = ["employee", "rule", "status"]
