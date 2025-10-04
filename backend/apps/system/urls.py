from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AsyncRoutesView,
    DeptInfoViewSet,
    DingTalkAttendanceViewSet,
    DingTalkConfigView,
    DingTalkDepartmentViewSet,
    DingTalkFullSyncView,
    DingTalkSyncAttendanceView,
    DingTalkSyncDepartmentsView,
    DingTalkSyncInfoView,
    DingTalkSyncLogViewSet,
    DingTalkSyncUsersView,
    DingTalkTestConnectionView,
    DingTalkUserViewSet,
    MenuMetaViewSet,
    MenuViewSet,
    RoleViewSet,
)

router = DefaultRouter()
router.register("role", RoleViewSet, basename="role")
router.register("menu", MenuViewSet, basename="menu")
router.register("menumeta", MenuMetaViewSet, basename="menu-meta")
router.register("dept", DeptInfoViewSet, basename="dept-info")
router.register("dingtalk/logs", DingTalkSyncLogViewSet, basename="dingtalk-logs")
router.register("dingtalk/departments", DingTalkDepartmentViewSet, basename="dingtalk-departments")
router.register("dingtalk/users", DingTalkUserViewSet, basename="dingtalk-users")
router.register("dingtalk/attendances", DingTalkAttendanceViewSet, basename="dingtalk-attendances")

urlpatterns = [
    path("asyncroutes/", AsyncRoutesView.as_view(), name="AsyncRoutesView"),
    path("dingtalk/config/", DingTalkConfigView.as_view(), name="dingtalk-config"),
    path("dingtalk/sync/info/", DingTalkSyncInfoView.as_view(), name="dingtalk-sync-info"),
    path("dingtalk/test-connection/", DingTalkTestConnectionView.as_view(), name="dingtalk-test"),
    path("dingtalk/sync/departments/", DingTalkSyncDepartmentsView.as_view(), name="dingtalk-sync-departments"),
    path("dingtalk/sync/users/", DingTalkSyncUsersView.as_view(), name="dingtalk-sync-users"),
    path("dingtalk/sync/full/", DingTalkFullSyncView.as_view(), name="dingtalk-sync-full"),
    path("dingtalk/sync/attendance/", DingTalkSyncAttendanceView.as_view(), name="dingtalk-sync-attendance"),
    path("", include(router.urls)),
]
