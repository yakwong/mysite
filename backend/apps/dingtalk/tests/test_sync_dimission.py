from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.dingtalk.constants import DEFAULT_DIMISSION_ROSTER_FIELDS
from apps.dingtalk.models import DingTalkConfig, DingTalkDimissionUser
from apps.dingtalk.services.sync import SyncService


class SyncDimissionUsersTests(TestCase):
    def setUp(self):
        self.config = DingTalkConfig.load()
        self.config.app_key = "test-key"
        self.config.app_secret = "test-secret"
        self.config.enabled = True
        self.config.save()

    @patch("apps.dingtalk.services.sync.DingTalkClient.list_dimission_records", return_value=[])
    @patch("apps.dingtalk.services.sync.DingTalkClient.list_roster_infos")
    @patch("apps.dingtalk.services.sync.DingTalkClient.list_dimission_infos")
    @patch("apps.dingtalk.services.sync.DingTalkClient.list_dimission_userids")
    def test_sync_dimission_users_enriches_with_roster(
        self,
        mock_userids,
        mock_infos,
        mock_roster,
        mock_records,
    ):
        custom_fields = [
            "sys00-name",
            "sys00-mobile",
            "sys00-jobNumber",
            "sys00-mainDept",
            "sys00-email",
        ]
        self.config.schedule = {"dimission_roster_fields": custom_fields}
        self.config.save(update_fields=["schedule"])

        mock_userids.return_value = ["user-1"]
        mock_infos.return_value = [{"userid": "user-1"}]
        mock_roster.return_value = {
            "user-1": {
                "sys00-name": {"value": "张三"},
                "sys00-mobile": {"value": "13900001234"},
                "sys00-jobNumber": {"value": "J001"},
                "sys00-mainDept": {"value": "200", "label": "研发中心"},
                "sys00-email": {"value": "tester@example.com"},
            }
        }

        service = SyncService(self.config)
        result = service.sync_dimission_users()

        self.assertEqual(result["count"], 1)
        dimission = DingTalkDimissionUser.objects.get(userid="user-1")
        self.assertEqual(dimission.name, "张三")
        self.assertEqual(dimission.mobile, "13900001234")
        self.assertEqual(dimission.job_number, "J001")
        self.assertEqual(dimission.main_dept_id, 200)
        self.assertEqual(dimission.main_dept_name, "研发中心")
        self.assertEqual(dimission.config_id, self.config.id)
        self.assertEqual(dimission.source_info.get("employeeInfo", {}).get("name"), "张三")

        mock_userids.assert_called_once()
        mock_infos.assert_called_once()
        mock_roster.assert_called_once_with(["user-1"], field_codes=custom_fields)
        mock_records.assert_called_once()

    def test_get_dimission_roster_fields_default(self):
        self.config.schedule = {}
        self.config.save(update_fields=["schedule"])

        result = self.config.get_dimission_roster_fields()

        self.assertEqual(result, list(DEFAULT_DIMISSION_ROSTER_FIELDS))

    @override_settings(DINGTALK={"DIMISSION_ROSTER_FIELDS": ["sys00-name", "sys00-mobile"]})
    def test_get_dimission_roster_fields_override_settings(self):
        self.config.schedule = {}
        self.config.save(update_fields=["schedule"])

        result = self.config.get_dimission_roster_fields()

        self.assertEqual(result, ["sys00-name", "sys00-mobile"])

    def test_get_dimission_roster_fields_schedule_priority(self):
        self.config.schedule = {"dimission_roster_fields": "sys00-name, sys00-mobile , sys00-jobNumber"}
        self.config.save(update_fields=["schedule"])

        result = self.config.get_dimission_roster_fields()

        self.assertEqual(result, ["sys00-name", "sys00-mobile", "sys00-jobNumber"])
