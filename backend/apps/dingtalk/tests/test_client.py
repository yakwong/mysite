from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from apps.dingtalk.models import DingTalkConfig
from apps.dingtalk.services.client import DingTalkClient


class DingTalkClientAttendanceTests(TestCase):
    def setUp(self):
        self.config = DingTalkConfig.load()
        self.config.enabled = True
        self.config.app_key = "test-key"
        self.config.app_secret = "test-secret"
        self.config.save()

    @patch("apps.dingtalk.services.client.DingTalkClient._request")
    @patch("apps.dingtalk.services.client.DingTalkClient.get_access_token")
    def test_list_attendance_records_calls_correct_endpoint(self, mock_get_token, mock_request):
        mock_get_token.return_value = "token"
        mock_request.return_value = {"result": {"recordresult": []}}

        client = DingTalkClient(self.config)
        start = timezone.make_aware(datetime(2025, 9, 1, 0, 0, 0))
        end = timezone.make_aware(datetime(2025, 9, 1, 23, 59, 59))

        client.list_attendance_records(["user-a"], start_time=start, end_time=end)

        mock_request.assert_called_with(
            "POST",
            "/attendance/listRecord",
            data={
                "userIdList": ["user-a"],
                "userIds": ["user-a"],
                "checkDateFrom": "2025-09-01 00:00:00",
                "checkDateTo": "2025-09-01 23:59:59",
                "isI18n": False,
                "offset": 0,
                "limit": 50,
            },
            access_token="token",
        )

    @patch("apps.dingtalk.services.client.DingTalkClient._request")
    @patch("apps.dingtalk.services.client.DingTalkClient.get_access_token")
    def test_list_attendance_records_stop_when_has_more_false(self, mock_get_token, mock_request):
        mock_get_token.return_value = "token"
        mock_request.side_effect = [
            {"result": {"recordresult": [{"record_id": 1}, {"record_id": 2}], "hasMore": False}},
        ]

        client = DingTalkClient(self.config)
        start = timezone.make_aware(datetime(2025, 9, 1, 0, 0, 0))
        end = timezone.make_aware(datetime(2025, 9, 1, 23, 59, 59))

        records = client.list_attendance_records(["user-a", "user-b"], start_time=start, end_time=end)

        self.assertEqual(len(records), 2)
        self.assertEqual(mock_request.call_count, 1)
