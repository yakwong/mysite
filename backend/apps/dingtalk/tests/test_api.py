from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.dingtalk.models import DingTalkAttendanceRecord, DingTalkConfig, DingTalkSyncLog


class DingTalkAPITestCase(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="tester@example.com",
            username="tester",
            password="StrongPass!123",
        )
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        DingTalkConfig.load()
        self.client.force_authenticate(self.user)

    def test_get_config_list_contains_default(self):
        url = reverse("dingtalk-configs-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertGreaterEqual(len(payload["data"]), 1)  # type: ignore[index]
        self.assertEqual(payload["data"][0]["id"], "default")  # type: ignore[index]

    def test_update_config_resets_token_when_app_changed(self):
        config = DingTalkConfig.load()
        config.app_key = "old"
        config.app_secret = "old-secret"
        config.access_token = "token"
        config.access_token_expires_at = timezone.now() + timedelta(hours=1)
        config.save()

        url = reverse("dingtalk-configs-detail", args=[config.id])
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
        DingTalkConfig.load()
        url = reverse("dingtalk-sync-command-default")
        response = self.client.post(url, {"operation": "test_connection"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload = response.json()
        self.assertFalse(payload["success"])  # type: ignore[index]
        self.assertTrue(
            DingTalkSyncLog.objects.filter(operation="test_connection", status="failed").exists()
        )

    def test_test_connection_success(self):
        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = True
        config.save()

        def fake_get_access_token(self, force_refresh=False):  # noqa: ARG001 - 符合签名
            self.config.access_token = "fake-token"
            self.config.access_token_expires_at = timezone.now() + timedelta(minutes=30)
            self.config.save(update_fields=["access_token", "access_token_expires_at", "update_time"])
            return "fake-token"

        url = reverse("dingtalk-sync-command-default")
        with patch("apps.dingtalk.services.client.DingTalkClient.get_access_token", new=fake_get_access_token):
            response = self.client.post(url, {"operation": "test_connection"}, format="json")
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

        url = reverse("dingtalk-sync-command-default")
        response = self.client.post(url, {"operation": "sync_departments"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload = response.json()
        self.assertFalse(payload["success"])  # type: ignore[index]
        self.assertTrue(
            DingTalkSyncLog.objects.filter(operation="sync_departments", status="failed").exists()
        )

    @patch("apps.dingtalk.services.client.DingTalkClient.list_departments")
    def test_remote_department_preview(self, mock_list_departments):
        mock_list_departments.return_value = [
            {"dept_id": 1, "name": "总部"},
            {"dept_id": 2, "name": "研发"},
        ]
        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = True
        config.save()

        url = reverse("dingtalk-departments-preview-remote")
        response = self.client.get(f"{url}?config_id={config.id}&limit=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["total"], 2)  # type: ignore[index]
        self.assertEqual(len(payload["data"]), 1)  # type: ignore[arg-type]
        self.assertEqual(payload["data"][0]["dept_id"], 1)  # type: ignore[index]
        mock_list_departments.assert_called_once()

    @patch("apps.dingtalk.services.sync.SyncService.sync_attendance")
    def test_sync_attendance_endpoint(self, mock_sync_attendance):
        mock_sync_attendance.return_value = {"count": 5}
        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = True
        config.save()

        url = reverse("dingtalk-sync-command-default")
        payload = {
            "operation": "sync_attendance",
            "start": "2025-09-01T00:00:00",
            "end": "2025-09-01T23:59:59",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["data"]["count"], 5)  # type: ignore[index]
        mock_sync_attendance.assert_called_once()

    @patch("apps.dingtalk.services.sync.SyncService.preview_attendance")
    def test_preview_attendance_endpoint(self, mock_preview_attendance):
        mock_preview_attendance.return_value = [
            {
                "record_id": "rec-1",
                "config_id": "default",
                "userid": "user-a",
                "check_type": "OnDuty",
                "time_result": "Normal",
                "user_check_time": "2025-09-01T09:00:00+08:00",
                "work_date": "2025-09-01",
                "source_type": "test",
                "source_info": {"original": True},
            }
        ]

        config = DingTalkConfig.load()
        config.app_key = "key"
        config.app_secret = "secret"
        config.enabled = True
        config.save()

        response = self.client.get(
            f"/api/dingtalk/attendances/remote/?config_id={config.id}&start=2025-09-01T00:00:00&end=2025-09-01T23:59:59&userIds=user-a"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["data"]["count"], 1)  # type: ignore[index]
        self.assertEqual(payload["data"]["records"][0]["userid"], "user-a")  # type: ignore[index]
        mock_preview_attendance.assert_called_once()

    def test_attendance_record_persists(self):
        config = DingTalkConfig.load()
        config.enabled = True
        config.app_key = "key"
        config.app_secret = "secret"
        config.save()

        with patch("apps.dingtalk.services.sync.SyncService.sync_attendance", return_value={"count": 0}):
            response = self.client.post(
                reverse("dingtalk-sync-command-default"),
                {
                    "operation": "sync_attendance",
                    "start": "2025-09-01T00:00:00",
                    "end": "2025-09-01T23:59:59",
                },
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DingTalkAttendanceRecord.objects.count(), 0)

    @patch("apps.dingtalk.services.client.DingTalkClient.list_attendance_records")
    @patch("apps.dingtalk.services.client.DingTalkClient.get_access_token")
    def test_partial_attendance_sync_allowed_when_disabled(self, mock_get_token, mock_list_records):
        mock_get_token.return_value = "token"
        mock_list_records.return_value = [
            {
                "record_id": "rec-1",
                "userid": "user-a",
                "user_check_time": "2025-09-01T09:00:00",
                "check_type": "OnDuty",
                "time_result": "Normal",
                "work_date": "2025-09-01",
                "source_type": "test",
            }
        ]

        config = DingTalkConfig.load()
        config.enabled = False
        config.app_key = "key"
        config.app_secret = "secret"
        config.save()

        url = reverse("dingtalk-sync-command-default")
        response = self.client.post(
            url,
            {
                "operation": "sync_attendance",
                "start": "2025-09-01T00:00:00",
                "end": "2025-09-01T23:59:59",
                "userIds": ["user-a"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])  # type: ignore[index]
        self.assertEqual(payload["data"]["count"], 1)  # type: ignore[index]
        self.assertEqual(DingTalkAttendanceRecord.objects.count(), 1)
        mock_list_records.assert_called_once()
