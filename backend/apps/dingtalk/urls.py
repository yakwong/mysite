from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DeptBindingViewSet,
    DingTalkAttendanceViewSet,
    DingTalkCallbackView,
    DingTalkConfigViewSet,
    DingTalkDepartmentViewSet,
    DingTalkSyncLogViewSet,
    DingTalkUserViewSet,
    SyncCommandView,
    SyncCursorViewSet,
    UserBindingViewSet,
)

router = DefaultRouter()
router.register("configs", DingTalkConfigViewSet, basename="dingtalk-configs")
router.register("logs", DingTalkSyncLogViewSet, basename="dingtalk-logs")
router.register("departments", DingTalkDepartmentViewSet, basename="dingtalk-departments")
router.register("users", DingTalkUserViewSet, basename="dingtalk-users")
router.register("attendances", DingTalkAttendanceViewSet, basename="dingtalk-attendances")
router.register("cursors", SyncCursorViewSet, basename="dingtalk-cursors")
router.register("dept-bindings", DeptBindingViewSet, basename="dingtalk-dept-bindings")
router.register("user-bindings", UserBindingViewSet, basename="dingtalk-user-bindings")

urlpatterns = [
    path("", include(router.urls)),
    path("<str:config_id>/sync/", SyncCommandView.as_view(), name="dingtalk-sync-command"),
    path("sync/", SyncCommandView.as_view(), name="dingtalk-sync-command-default"),
    path("<str:config_id>/callbacks/", DingTalkCallbackView.as_view(), name="dingtalk-callback"),
]
