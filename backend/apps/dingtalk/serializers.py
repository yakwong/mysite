from __future__ import annotations

from rest_framework import serializers

from .constants import SyncOperation
from .models import (
    DeptBinding,
    DingTalkAttendanceRecord,
    DingTalkConfig,
    DingTalkDepartment,
    DingTalkSyncLog,
    DingTalkUser,
    SyncCursor,
    UserBinding,
)


class DingTalkConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DingTalkConfig
        fields = [
            "id",
            "name",
            "tenant_id",
            "app_key",
            "app_secret",
            "agent_id",
            "enabled",
            "sync_users",
            "sync_departments",
            "sync_attendance",
            "callback_url",
            "callback_token",
            "callback_aes_key",
            "schedule",
            "remark",
        ]
        extra_kwargs = {
            "app_secret": {"write_only": False},
        }


class DingTalkSyncInfoSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="last_sync_status", allow_blank=True, required=False)
    message = serializers.CharField(source="last_sync_message", allow_blank=True, required=False)
    lastSyncTime = serializers.DateTimeField(source="last_sync_time", allow_null=True, required=False)
    lastDeptSyncTime = serializers.DateTimeField(source="last_dept_sync_time", allow_null=True, required=False)
    lastUserSyncTime = serializers.DateTimeField(source="last_user_sync_time", allow_null=True, required=False)
    lastAttendanceSyncTime = serializers.DateTimeField(source="last_attendance_sync_time", allow_null=True, required=False)
    deptCount = serializers.IntegerField(source="last_dept_sync_count", read_only=True)
    userCount = serializers.IntegerField(source="last_user_sync_count", read_only=True)
    attendanceCount = serializers.IntegerField(source="last_attendance_sync_count", read_only=True)
    accessTokenExpiresAt = serializers.DateTimeField(source="access_token_expires_at", allow_null=True, required=False)

    class Meta:
        model = DingTalkConfig
        fields = [
            "status",
            "message",
            "lastSyncTime",
            "lastDeptSyncTime",
            "lastUserSyncTime",
            "lastAttendanceSyncTime",
            "deptCount",
            "userCount",
            "attendanceCount",
            "accessTokenExpiresAt",
        ]


class SyncCursorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncCursor
        fields = ["cursor_type", "value", "extra", "update_time"]


class DingTalkSyncLogSerializer(serializers.ModelSerializer):
    operationLabel = serializers.CharField(source="get_operation_display", read_only=True)
    statusLabel = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DingTalkSyncLog
        fields = [
            "id",
            "operation",
            "operationLabel",
            "status",
            "statusLabel",
            "level",
            "message",
            "detail",
            "stats",
            "retry_count",
            "next_retry_at",
            "create_time",
        ]


class DingTalkDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DingTalkDepartment
        fields = [
            "dept_id",
            "config_id",
            "name",
            "parent_id",
            "order",
            "leader_userid",
            "dept_type",
            "source_info",
            "create_time",
            "update_time",
        ]


class DingTalkUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DingTalkUser
        fields = [
            "userid",
            "config_id",
            "name",
            "mobile",
            "email",
            "active",
            "job_number",
            "title",
            "dept_ids",
            "unionid",
            "remark",
            "source_info",
            "create_time",
            "update_time",
        ]


class DingTalkAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DingTalkAttendanceRecord
        fields = [
            "record_id",
            "config_id",
            "userid",
            "check_type",
            "time_result",
            "user_check_time",
            "work_date",
            "source_type",
            "source_info",
            "create_time",
            "update_time",
        ]


class DingTalkAttendancePreviewSerializer(serializers.Serializer):
    record_id = serializers.CharField()
    config_id = serializers.CharField()
    userid = serializers.CharField()
    check_type = serializers.CharField(allow_blank=True, required=False)
    time_result = serializers.CharField(allow_blank=True, required=False)
    user_check_time = serializers.DateTimeField()
    work_date = serializers.DateField(allow_null=True, required=False)
    source_type = serializers.CharField(allow_blank=True, required=False)
    source_info = serializers.JSONField(required=False)


class DeptBindingSerializer(serializers.ModelSerializer):
    deptName = serializers.CharField(source="dingtalk_dept.name", read_only=True)

    class Meta:
        model = DeptBinding
        fields = ["id", "config_id", "dingtalk_dept_id", "deptName", "local_dept_code", "create_time"]


class UserBindingSerializer(serializers.ModelSerializer):
    userName = serializers.CharField(source="dingtalk_user.name", read_only=True)

    class Meta:
        model = UserBinding
        fields = ["id", "config_id", "dingtalk_user_id", "userName", "local_user_id", "create_time"]


class SyncCommandSerializer(serializers.Serializer):
    operation = serializers.ChoiceField(choices=[(item.value, item.name) for item in SyncOperation])
    mode = serializers.ChoiceField(choices=(("full", "全量"), ("incremental", "增量")), default="full")
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    userIds = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=False)
