from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceRuleViewSet,
    AttendanceSummaryViewSet,
    DepartmentViewSet,
    EmployeeViewSet,
    PayrollRecordViewSet,
    PayrollRuleViewSet,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="hr-department")
router.register("employees", EmployeeViewSet, basename="hr-employee")
router.register("attendance/rules", AttendanceRuleViewSet, basename="hr-attendance-rule")
router.register("attendance/summary", AttendanceSummaryViewSet, basename="hr-attendance-summary")
router.register("payroll/rules", PayrollRuleViewSet, basename="hr-payroll-rule")
router.register("payroll/records", PayrollRecordViewSet, basename="hr-payroll-record")

urlpatterns = [
    path("", include(router.urls)),
]
