from __future__ import annotations

import json
import logging

from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.response import CustomResponse
from utils.viewset import CustomModelViewSet

from .constants import SyncOperation
from .filters import (
    DingTalkAttendanceFilter,
    DingTalkDepartmentFilter,
    DingTalkSyncLogFilter,
    DingTalkUserFilter,
)
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
from .permissions import CanManageDingTalk, CanViewDingTalk
from .serializers import (
    DeptBindingSerializer,
    DingTalkAttendanceSerializer,
    DingTalkConfigSerializer,
    DingTalkDepartmentSerializer,
    DingTalkSyncInfoSerializer,
    DingTalkSyncLogSerializer,
    DingTalkUserSerializer,
    SyncCommandSerializer,
    SyncCursorSerializer,
    UserBindingSerializer,
)
from .services import (
    DingTalkAPIError,
    DingTalkConfigurationError,
    DingTalkDisabledError,
    SyncService,
)


def _handle_exception(service: SyncService, operation: SyncOperation, exc: Exception):
    message = str(exc)
    detail = ""
    response_status = status.HTTP_400_BAD_REQUEST

    if isinstance(exc, DingTalkAPIError):
        detail = json.dumps(getattr(exc, "payload", {}), ensure_ascii=False) if getattr(exc, "payload", None) else ""
        response_status = status.HTTP_502_BAD_GATEWAY
        service._handle_failure(operation, exc, detail=detail)  # noqa: SLF001
    elif isinstance(exc, DingTalkConfigurationError):
        service._handle_failure(operation, exc)  # noqa: SLF001
    elif isinstance(exc, DingTalkDisabledError):
        service._handle_failure(operation, exc)  # noqa: SLF001
    else:
        response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        service._handle_failure(operation, exc)  # noqa: SLF001

    return CustomResponse(success=False, data=None, msg=message, status=response_status)


class DingTalkConfigViewSet(CustomModelViewSet):
    queryset = DingTalkConfig.objects.all().order_by("id")
    serializer_class = DingTalkConfigSerializer
    permission_classes = [IsAuthenticated, CanManageDingTalk]

    def perform_update(self, serializer):
        instance = serializer.instance
        previous_app_key = instance.app_key
        previous_app_secret = instance.app_secret
        result = serializer.save()
        if previous_app_key != result.app_key or previous_app_secret != result.app_secret:
            result.reset_access_token()
        return result

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated, CanViewDingTalk])
    def sync_info(self, request, pk=None):
        config = self.get_object()
        data = DingTalkSyncInfoSerializer(config).data
        return CustomResponse(success=True, data=data, msg="成功获取同步信息")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, CanManageDingTalk])
    def reset_token(self, request, pk=None):
        config = self.get_object()
        config.reset_access_token()
        return CustomResponse(success=True, data=None, msg="访问令牌已重置")


class SyncCommandView(APIView):
    permission_classes = [IsAuthenticated, CanManageDingTalk]

    def post(self, request, config_id: str | None = None):
        serializer = SyncCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = DingTalkConfig.load(config_id)
        service = SyncService(config)
        operation = SyncOperation(serializer.validated_data["operation"])
        mode = serializer.validated_data.get("mode", "full")
        start = serializer.validated_data.get("start")
        end = serializer.validated_data.get("end")
        user_ids = serializer.validated_data.get("userIds")

        try:
            if operation == SyncOperation.TEST_CONNECTION:
                data = service.test_connection()
                return CustomResponse(success=True, data=data, msg="钉钉连接正常")
            if operation == SyncOperation.SYNC_DEPARTMENTS:
                data = service.sync_departments(mode=mode)
                return CustomResponse(success=True, data=data, msg="部门同步完成")
            if operation == SyncOperation.SYNC_USERS:
                data = service.sync_users(mode=mode)
                return CustomResponse(success=True, data=data, msg="用户同步完成")
            if operation == SyncOperation.SYNC_ATTENDANCE:
                if not start or not end:
                    return CustomResponse(success=False, data=None, msg="请提供 start 与 end 时间", status=status.HTTP_400_BAD_REQUEST)
                if start.tzinfo is None:
                    start = timezone.make_aware(start, timezone.get_current_timezone())
                if end.tzinfo is None:
                    end = timezone.make_aware(end, timezone.get_current_timezone())
                data = service.sync_attendance(start, end, mode=mode, user_ids=user_ids)
                return CustomResponse(success=True, data=data, msg="考勤同步完成")
            if operation == SyncOperation.FULL_SYNC:
                data = service.full_sync()
                return CustomResponse(success=True, data=data, msg="全量同步完成")
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_exception(service, operation, exc)
        return CustomResponse(success=False, data=None, msg="暂不支持的操作", status=status.HTTP_400_BAD_REQUEST)


class DingTalkSyncLogViewSet(CustomModelViewSet):
    queryset = DingTalkSyncLog.objects.select_related("config").all()
    serializer_class = DingTalkSyncLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DingTalkSyncLogFilter
    permission_classes = [IsAuthenticated, CanViewDingTalk]


class DingTalkDepartmentViewSet(CustomModelViewSet):
    queryset = DingTalkDepartment.objects.select_related("config").all().order_by("dept_id")
    serializer_class = DingTalkDepartmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DingTalkDepartmentFilter
    permission_classes = [IsAuthenticated, CanViewDingTalk]

    @action(detail=False, methods=["get"], url_path="remote")
    def preview_remote(self, request, *args, **kwargs):
        config_id = request.query_params.get("config_id") or DingTalkConfig.DEFAULT_ID
        root_dept_id = request.query_params.get("root_dept_id") or 1
        try:
            root_dept_id = int(root_dept_id)
        except (TypeError, ValueError):
            root_dept_id = 1
        config = DingTalkConfig.load(config_id)
        service = SyncService(config)
        try:
            departments = service.client.list_departments(root_dept_id)
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_exception(service, SyncOperation.SYNC_DEPARTMENTS, exc)
        limit = request.query_params.get("limit")
        total = len(departments)
        try:
            limit_value = min(int(limit), total) if limit else total
        except ValueError:
            limit_value = total
        data = departments[:limit_value]
        return CustomResponse(success=True, data=data, msg="成功获取实时部门列表", page=1, limit=limit_value, total=total)


class DingTalkUserViewSet(CustomModelViewSet):
    queryset = DingTalkUser.objects.select_related("config").all().order_by("userid")
    serializer_class = DingTalkUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DingTalkUserFilter
    permission_classes = [IsAuthenticated, CanViewDingTalk]

    @action(detail=False, methods=["get"], url_path="remote")
    def preview_remote(self, request, *args, **kwargs):
        config_id = request.query_params.get("config_id") or DingTalkConfig.DEFAULT_ID
        keyword = request.query_params.get("keyword")
        limit = request.query_params.get("limit")
        config = DingTalkConfig.load(config_id)
        service = SyncService(config)
        try:
            departments = service.client.list_departments(1)
            dept_ids: set[int] = set()
            for dept in departments:
                value = dept.get("dept_id") or dept.get("id")
                if value is None:
                    continue
                try:
                    dept_ids.add(int(value))
                except (TypeError, ValueError):
                    continue
            if not dept_ids:
                dept_ids.add(1)
            users = service.client.list_all_users(dept_ids)
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_exception(service, SyncOperation.SYNC_USERS, exc)

        if keyword:
            keyword_lower = keyword.lower()
            filtered: list[dict[str, Any]] = []
            for user in users:
                if not isinstance(user, dict):
                    continue
                name = str(user.get("name") or "").lower()
                mobile = str(user.get("mobile") or "").lower()
                userid = str(user.get("userid") or "").lower()
                email = str(user.get("email") or "").lower()
                if any(keyword_lower in field for field in (name, mobile, userid, email)):
                    filtered.append(user)
            users = filtered

        total = len(users)
        try:
            limit_value = min(int(limit), total) if limit else total
        except ValueError:
            limit_value = total
        data = users[:limit_value]
        return CustomResponse(success=True, data=data, msg="成功获取实时用户列表", page=1, limit=limit_value, total=total)


class DingTalkAttendanceViewSet(CustomModelViewSet):
    queryset = DingTalkAttendanceRecord.objects.select_related("config").all()
    serializer_class = DingTalkAttendanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DingTalkAttendanceFilter
    permission_classes = [IsAuthenticated, CanViewDingTalk]

    @action(detail=False, methods=["get"], url_path="remote")
    def preview_remote(self, request, *args, **kwargs):
        config_id = request.query_params.get("config_id") or DingTalkConfig.DEFAULT_ID
        config = DingTalkConfig.load(config_id)
        service = SyncService(config)

        now = timezone.now()
        tz = timezone.get_current_timezone()

        def _parse(value: str | None, fallback: datetime) -> datetime:
            if not value:
                return fallback
            parsed = parse_datetime(value)
            if parsed is None:
                try:
                    parsed = datetime.fromisoformat(value)
                except ValueError:
                    return fallback
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, tz)
            return parsed

        start_default = now - timedelta(days=7)
        end_default = now
        start = _parse(request.query_params.get("start"), start_default)
        end = _parse(request.query_params.get("end"), end_default)

        user_ids = request.query_params.getlist("userIds") or request.query_params.getlist("userIds[]")
        if not user_ids:
            bracket_values = [value for key, value in request.query_params.lists() if key.startswith("userIds[")]
            if bracket_values:
                user_ids = [item for sublist in bracket_values for item in sublist]
        if not user_ids:
            user_ids_param = request.query_params.get("userIds")
            if user_ids_param:
                user_ids = [item.strip() for item in user_ids_param.split(",") if item.strip()]
        if user_ids:
            if len(user_ids) == 1 and "," in (user_ids[0] or ""):
                user_ids = [item.strip() for item in user_ids[0].split(",") if item.strip()]
            user_ids = list(dict.fromkeys(item.strip() for item in user_ids if item and item.strip()))

        try:
            preview_data = service.preview_attendance(start, end, user_ids=user_ids or None)
            return CustomResponse(
                success=True,
                data={"records": preview_data, "count": len(preview_data)},
                msg="成功获取考勤预览",
            )
        except (DingTalkAPIError, DingTalkConfigurationError, DingTalkDisabledError) as exc:
            return _handle_exception(service, SyncOperation.SYNC_ATTENDANCE, exc)


class SyncCursorViewSet(CustomModelViewSet):
    queryset = SyncCursor.objects.select_related("config").all()
    serializer_class = SyncCursorSerializer
    permission_classes = [IsAuthenticated, CanManageDingTalk]


class DeptBindingViewSet(CustomModelViewSet):
    queryset = DeptBinding.objects.select_related("config", "dingtalk_dept").all()
    serializer_class = DeptBindingSerializer
    permission_classes = [IsAuthenticated, CanManageDingTalk]


class UserBindingViewSet(CustomModelViewSet):
    queryset = UserBinding.objects.select_related("config", "dingtalk_user").all()
    serializer_class = UserBindingSerializer
    permission_classes = [IsAuthenticated, CanManageDingTalk]


class DingTalkCallbackView(APIView):
    permission_classes = []

    def post(self, request, config_id: str | None = None):
        config = DingTalkConfig.load(config_id)
        if not config.callback_token or not config.callback_aes_key:
            return CustomResponse(success=False, data=None, msg="未配置回调 Token/AES Key", status=status.HTTP_400_BAD_REQUEST)
        # 简单验签留空实现：项目可在此处加入实际验签逻辑
        logger = logging.getLogger(__name__)
        logger.info("收到钉钉回调 config=%s payload=%s", config.id, request.data)
        return CustomResponse(success=True, data=None, msg="回调已接收")
