from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from apps.dingtalk.models import DingTalkConfig
from apps.dingtalk.services.client import DingTalkClient
from apps.dingtalk.services.exceptions import DingTalkAPIError


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


class DingTalkClientDimissionTests(TestCase):
    def setUp(self):
        self.config = DingTalkConfig.load()
        self.config.enabled = True
        self.config.app_key = "test-key"
        self.config.app_secret = "test-secret"
        self.config.save()

    @patch("apps.dingtalk.services.client.DingTalkClient._request_open_api")
    def test_list_dimission_userids_prefers_open_api(self, mock_open_api):
        mock_open_api.side_effect = [
            {"userIdList": ["u1", "u2"], "hasMore": True, "nextToken": "n1"},
            {"userIdList": ["u2", "u3"], "hasMore": False},
        ]

        client = DingTalkClient(self.config)
        result = client.list_dimission_userids()

        self.assertEqual(result, ["u1", "u2", "u3"])
        self.assertEqual(mock_open_api.call_count, 2)

    @patch("apps.dingtalk.services.client.DingTalkClient._request")
    @patch("apps.dingtalk.services.client.DingTalkClient.get_access_token")
    @patch("apps.dingtalk.services.client.DingTalkClient._request_open_api")
    def test_list_dimission_userids_fallback_legacy(self, mock_open_api, mock_get_token, mock_request):
        mock_open_api.side_effect = DingTalkAPIError("no permission")
        mock_get_token.return_value = "token"
        mock_request.side_effect = [
            {"result": {"userid_list": ["a"], "hasMore": True}},
            {"result": {"userid_list": ["b"], "hasMore": False}},
        ]

        client = DingTalkClient(self.config)
        result = client.list_dimission_userids()

        self.assertEqual(result, ["a", "b"])
        self.assertEqual(mock_open_api.call_count, 1)
        self.assertEqual(mock_request.call_count, 2)

    @patch("apps.dingtalk.services.client.DingTalkClient._request_open_api")
    def test_list_dimission_infos_open_api(self, mock_open_api):
        mock_open_api.return_value = {
            "result": [
                {"userid": "u1", "name": "张三"},
                {"userid": "u2", "name": "李四"},
            ]
        }

        client = DingTalkClient(self.config)
        infos = client.list_dimission_infos(["u1", "u2"])

        self.assertEqual(len(infos), 2)
        self.assertEqual(infos[0]["userid"], "u1")
        mock_open_api.assert_called_once()
        method, path = mock_open_api.call_args[0]
        params = mock_open_api.call_args.kwargs.get("params")
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/v1.0/hrm/employees/dimissionInfos")
        self.assertIn("userIdList", params)

    @patch("apps.dingtalk.services.client.DingTalkClient._request")
    @patch("apps.dingtalk.services.client.DingTalkClient.get_access_token")
    @patch("apps.dingtalk.services.client.DingTalkClient._request_open_api")
    def test_list_dimission_infos_fallback_legacy(self, mock_open_api, mock_get_token, mock_request):
        mock_open_api.side_effect = DingTalkAPIError("open api disabled")
        mock_get_token.return_value = "token"
        mock_request.return_value = {"result": {"data_list": [{"userid": "u1"}]}}

        client = DingTalkClient(self.config)
        infos = client.list_dimission_infos(["u1"])

        self.assertEqual(len(infos), 1)
        self.assertEqual(infos[0]["userid"], "u1")
        self.assertEqual(mock_open_api.call_count, 1)
        self.assertEqual(mock_request.call_count, 1)

    @patch("apps.dingtalk.services.client.DingTalkClient._request_open_api")
    def test_list_dimission_records_fallback_for_invalid_max_results(self, mock_open_api):
        mock_open_api.side_effect = [
            DingTalkAPIError(
                "Specified parameter maxResults is not valid.(code=InvalidmaxResults)",
                payload={"code": "InvalidmaxResults"},
            ),
            {"records": [{"userId": "u1"}]},
        ]

        client = DingTalkClient(self.config)
        records = client.list_dimission_records(max_results=200)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["userId"], "u1")
        self.assertEqual(mock_open_api.call_count, 2)
        first_params = mock_open_api.call_args_list[0].kwargs["params"]
        second_params = mock_open_api.call_args_list[1].kwargs["params"]
        self.assertEqual(first_params["maxResults"], 50)
        self.assertEqual(second_params["maxResults"], 20)

    @patch("apps.dingtalk.services.client.DingTalkClient._list_roster_infos_open_api")
    def test_list_roster_infos_collects_fields(self, mock_open_api):
        mock_open_api.return_value = [
            {
                "userId": "u1",
                "fieldDataList": [
                    {"fieldCode": "sys00-name", "fieldValueList": [{"value": "张三"}]},
                    {
                        "fieldCode": "sys00-mainDept",
                        "fieldValueList": [{"value": "200", "label": "研发部"}],
                    },
                ],
            }
        ]

        client = DingTalkClient(self.config)
        result = client.list_roster_infos(["u1"])

        self.assertIn("u1", result)
        self.assertEqual(result["u1"]["sys00-name"]["value"], "张三")
        self.assertEqual(result["u1"]["sys00-mainDept"]["label"], "研发部")
        mock_open_api.assert_called_once()

    @patch("apps.dingtalk.services.client.DingTalkClient._list_roster_infos_legacy")
    @patch("apps.dingtalk.services.client.DingTalkClient._list_roster_infos_open_api")
    def test_list_roster_infos_fallback_legacy(self, mock_open_api, mock_legacy):
        mock_open_api.side_effect = DingTalkAPIError("open api disabled")
        mock_legacy.return_value = [
            {
                "userid": "u2",
                "field_data_list": [
                    {
                        "field_code": "sys00-mobile",
                        "field_value_list": [
                            {"value": "13800001234"},
                        ],
                    }
                ],
            }
        ]

        client = DingTalkClient(self.config)
        result = client.list_roster_infos(["u2"])

        self.assertIn("u2", result)
        self.assertEqual(result["u2"]["sys00-mobile"]["value"], "13800001234")
        self.assertEqual(mock_open_api.call_count, 1)
        self.assertEqual(mock_legacy.call_count, 1)
