from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework import serializers

from .constants import (
    ATTENDANCE_CHECK_TYPE_LABELS,
    ATTENDANCE_TIME_RESULT_LABELS,
    SyncOperation,
)
from .models import (
    DeptBinding,
    DingTalkAttendanceRecord,
    DingTalkConfig,
    DingTalkDepartment,
    DingTalkDimissionUser,
    DingTalkSyncLog,
    DingTalkUser,
    SyncCursor,
    UserBinding,
)


def _ensure_list(instance: Any) -> list[Any]:
    if instance is None:
        return []
    if isinstance(instance, QuerySet):
        return list(instance)
    if isinstance(instance, (list, tuple, set)):
        return list(instance)
    return [instance]


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
    lastDimissionSyncTime = serializers.DateTimeField(source="last_dimission_sync_time", allow_null=True, required=False)
    deptCount = serializers.IntegerField(source="last_dept_sync_count", read_only=True)
    userCount = serializers.IntegerField(source="last_user_sync_count", read_only=True)
    attendanceCount = serializers.IntegerField(source="last_attendance_sync_count", read_only=True)
    dimissionCount = serializers.IntegerField(source="last_dimission_sync_count", read_only=True)
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
            "lastDimissionSyncTime",
            "deptCount",
            "userCount",
            "attendanceCount",
            "dimissionCount",
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
    dept_names = serializers.SerializerMethodField()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._dept_name_cache: dict[tuple[str, int], str] = {}
        instance_source = kwargs.get("instance")
        if instance_source is None and args:
            instance_source = args[0]
        instances = _ensure_list(instance_source)
        if not instances:
            return
        config_ids: set[str] = set()
        dept_ids: set[int] = set()
        for item in instances:
            if not isinstance(item, DingTalkUser):
                continue
            if item.config_id:
                config_ids.add(item.config_id)
            for raw_id in item.dept_ids or []:
                try:
                    value = int(raw_id)
                except (TypeError, ValueError):
                    continue
                dept_ids.add(value)
        if not config_ids or not dept_ids:
            return
        departments = DingTalkDepartment.objects.filter(config_id__in=config_ids, dept_id__in=dept_ids).only("dept_id", "name", "config_id")
        for dept in departments:
            key = (dept.config_id, int(dept.dept_id))
            self._dept_name_cache[key] = dept.name

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
            "dept_names",
            "unionid",
            "remark",
            "source_info",
            "create_time",
            "update_time",
        ]

    def get_dept_names(self, obj: DingTalkUser) -> list[str]:
        names: list[str] = []
        for raw_id in obj.dept_ids or []:
            try:
                dept_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            key = (obj.config_id, dept_id)
            if key not in self._dept_name_cache:
                department = (
                    DingTalkDepartment.objects.filter(config_id=obj.config_id, dept_id=dept_id)
                    .only("name")
                    .first()
                )
                if department:
                    self._dept_name_cache[key] = department.name
            name = self._dept_name_cache.get(key)
            if name:
                names.append(name)
        return names


class DingTalkDimissionUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DingTalkDimissionUser
        fields = [
            "id",
            "userid",
            "config_id",
            "name",
            "mobile",
            "job_number",
            "main_dept_id",
            "main_dept_name",
            "handover_userid",
            "last_work_day",
            "leave_time",
            "leave_reason",
            "reason_type",
            "reason_memo",
            "pre_status",
            "status",
            "voluntary_reasons",
            "passive_reasons",
            "dept_ids",
            "source_info",
            "create_time",
            "update_time",
        ]


class DingTalkAttendanceSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    check_type_label = serializers.SerializerMethodField()
    time_result_label = serializers.SerializerMethodField()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._user_name_cache: dict[tuple[str, str], str] = {}
        instance_source = kwargs.get("instance")
        if instance_source is None and args:
            instance_source = args[0]
        instances = _ensure_list(instance_source)
        if not instances:
            return
        config_ids: set[str] = set()
        user_ids: set[str] = set()
        for item in instances:
            if not isinstance(item, DingTalkAttendanceRecord):
                continue
            if item.config_id:
                config_ids.add(item.config_id)
            if item.userid:
                user_ids.add(item.userid)
        if not config_ids or not user_ids:
            return
        users = DingTalkUser.objects.filter(config_id__in=config_ids, userid__in=user_ids).only("userid", "name", "config_id")
        for user in users:
            self._user_name_cache[(user.config_id, user.userid)] = user.name

    class Meta:
        model = DingTalkAttendanceRecord
        fields = [
            "record_id",
            "config_id",
            "userid",
            "user_name",
            "check_type",
            "check_type_label",
            "time_result",
            "time_result_label",
            "user_check_time",
            "work_date",
            "source_type",
            "source_info",
            "create_time",
            "update_time",
        ]

    def get_user_name(self, obj: DingTalkAttendanceRecord) -> str:
        key = (obj.config_id, obj.userid)
        if key not in self._user_name_cache and obj.userid:
            user = (
                DingTalkUser.objects.filter(config_id=obj.config_id, userid=obj.userid)
                .only("name")
                .first()
            )
            if user:
                self._user_name_cache[key] = user.name
        return self._user_name_cache.get(key, "")

    def get_check_type_label(self, obj: DingTalkAttendanceRecord) -> str:
        if not obj.check_type:
            return ""
        return ATTENDANCE_CHECK_TYPE_LABELS.get(obj.check_type, obj.check_type)

    def get_time_result_label(self, obj: DingTalkAttendanceRecord) -> str:
        if not obj.time_result:
            return ""
        return ATTENDANCE_TIME_RESULT_LABELS.get(obj.time_result, obj.time_result)


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
