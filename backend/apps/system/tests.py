from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DingTalkConfig, DingTalkSyncLog, DingTalkAttendanceRecord


class DingTalkAPITestCase(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="tester@example.com",
            username="tester",
            password="StrongPass!123",
        )
        self.client.force_authenticate(self.user)

    def test_get_config_creates_default(self):
        url = reverse("dingtalk-config")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["data"]["config"]["id"], "default")  # type: ignore[index]

    def test_update_config_resets_token_when_app_changed(self):
        config = DingTalkConfig.load()
        config.app_key = "old"  # noqa: S105 (测试数据)
        config.app_secret = "old-secret"  # noqa: S105
        config.access_token = "token"
        config.access_token_expires_at = timezone.now() + timedelta(hours=1)
        config.save()

        url = reverse("dingtalk-config")
        payload = {
            "app_key": "new-key",
            "app_secret": "new-secret",
            "agent_id": "123",
            "enabled": True,
            "sync_users": True,
            "sync_departments": True,
        }
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        config.refresh_from_db()
        self.assertEqual(config.app_key, "new-key")
        self.assertEqual(config.access_token, "")
        self.assertIsNone(config.access_token_expires_at)

    def test_test_connection_missing_configuration(self):
        DingTalkConfig.load()  # ensure config exists but未配置密钥
        url = reverse("dingtalk-test")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload = response.json()
        self.assertFalse(payload["success"])  # type: ignore[index]
        self.assertTrue(DingTalkSyncLog.objects.filter(operation="test_connection", status="failed").exists())

    def test_test_connection_success(self):
        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = True
        config.save()

        def fake_get_access_token(self, force_refresh=False):  # noqa: ARG001 - 匹配签名
            self.config.access_token = "fake-token"
            self.config.access_token_expires_at = timezone.now() + timedelta(minutes=30)
            self.config.save(update_fields=["access_token", "access_token_expires_at", "update_time"])
            return "fake-token"

        url = reverse("dingtalk-test")
        with patch("apps.system.services.dingtalk.DingTalkClient.get_access_token", new=fake_get_access_token):
            response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["data"]["accessToken"], "fake-token")  # type: ignore[index]
        self.assertTrue(
            DingTalkSyncLog.objects.filter(operation="test_connection", status="success").exists()
        )

    def test_sync_departments_returns_400_when_disabled(self):
        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = False
        config.save()

        url = reverse("dingtalk-sync-departments")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload = response.json()
        self.assertFalse(payload["success"])  # type: ignore[index]
        self.assertTrue(
            DingTalkSyncLog.objects.filter(operation="sync_departments", status="failed").exists()
        )

    @patch("apps.system.views.DingTalkService.preview_departments")
    def test_remote_department_preview(self, mock_preview):
        mock_preview.return_value = [
            {"dept_id": 1, "name": "总部"},
            {"dept_id": 2, "name": "研发"},
        ]
        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = True
        config.save()

        url = reverse("dingtalk-departments-list")
        response = self.client.get(f"{url}?source=remote&limit=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["total"], 2)  # type: ignore[index]
        self.assertEqual(len(payload["data"]), 1)  # type: ignore[arg-type]
        self.assertEqual(payload["data"][0]["dept_id"], 1)  # type: ignore[index]
        mock_preview.assert_called_once_with(root_dept_id=1)

    @patch("apps.system.views.DingTalkService.sync_attendance")
    def test_sync_attendance_endpoint(self, mock_sync_attendance):
        mock_sync_attendance.return_value = {"count": 5}
        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = True
        config.save()

        url = reverse("dingtalk-sync-attendance")
        payload = {"start": "2025-09-01T00:00:00", "end": "2025-09-01T23:59:59"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["data"]["count"], 5)  # type: ignore[index]
        mock_sync_attendance.assert_called_once()
