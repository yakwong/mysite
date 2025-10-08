from __future__ import annotations

import django_filters

from .models import (
    DingTalkAttendanceRecord,
    DingTalkDepartment,
    DingTalkDimissionUser,
    DingTalkSyncLog,
    DingTalkUser,
)


class DingTalkSyncLogFilter(django_filters.FilterSet):
    operation = django_filters.CharFilter(field_name="operation")
    status = django_filters.CharFilter(field_name="status")
    level = django_filters.CharFilter(field_name="level")
    config_id = django_filters.CharFilter(field_name="config_id")
    created_after = django_filters.DateTimeFilter(field_name="create_time", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="create_time", lookup_expr="lte")

    class Meta:
        model = DingTalkSyncLog
        fields = ["operation", "status", "level", "config_id"]


class DingTalkDepartmentFilter(django_filters.FilterSet):
    config_id = django_filters.CharFilter(field_name="config_id")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = DingTalkDepartment
        fields = ["config_id", "name", "parent_id"]


class DingTalkUserFilter(django_filters.FilterSet):
    config_id = django_filters.CharFilter(field_name="config_id")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    mobile = django_filters.CharFilter(field_name="mobile", lookup_expr="icontains")

    class Meta:
        model = DingTalkUser
        fields = ["config_id", "name", "mobile"]


class DingTalkAttendanceFilter(django_filters.FilterSet):
    config_id = django_filters.CharFilter(field_name="config_id")
    userid = django_filters.CharFilter(field_name="userid")
    start = django_filters.DateTimeFilter(field_name="user_check_time", lookup_expr="gte")
    end = django_filters.DateTimeFilter(field_name="user_check_time", lookup_expr="lte")

    class Meta:
        model = DingTalkAttendanceRecord
        fields = ["config_id", "userid", "start", "end"]


class DingTalkDimissionUserFilter(django_filters.FilterSet):
    config_id = django_filters.CharFilter(field_name="config_id")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    mobile = django_filters.CharFilter(field_name="mobile", lookup_expr="icontains")
    userid = django_filters.CharFilter(field_name="userid", lookup_expr="icontains")

    class Meta:
        model = DingTalkDimissionUser
        fields = ["config_id", "name", "mobile", "userid"]
