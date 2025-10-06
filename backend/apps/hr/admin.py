from django.contrib import admin

from .models import AttendanceRule, AttendanceSummary, Department, Employee, PayrollRecord, PayrollRule


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "status", "manager", "config_id")
    list_filter = ("status", "config_id")
    search_fields = ("name", "code")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "job_number", "department", "employment_status", "config_id")
    list_filter = ("employment_status", "employment_type", "department")
    search_fields = ("name", "job_number")


@admin.register(AttendanceRule)
class AttendanceRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "workday_start", "workday_end")
    search_fields = ("name",)


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ("employee", "period_start", "period_end", "status")
    list_filter = ("status",)
    search_fields = ("employee__name", "employee__job_number")


@admin.register(PayrollRule)
class PayrollRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "overtime_rate", "tax_rate")
    search_fields = ("name",)


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "period_start", "period_end", "net_salary", "status")
    list_filter = ("status",)
    search_fields = ("employee__name", "employee__job_number")
