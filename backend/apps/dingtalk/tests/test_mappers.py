from datetime import datetime, timezone as dt_timezone

from django.test import SimpleTestCase
from django.utils import timezone

from apps.dingtalk.services.mappers import map_attendance, map_dimission


class MapAttendanceTests(SimpleTestCase):
    def test_map_attendance_accepts_epoch_milliseconds(self):
        milliseconds = 1759352400000  # 2025-10-01 07:00:00 UTC
        payload = {
            "userid": "user-1",
            "user_check_time": milliseconds,
            "record_id": "record-1",
            "check_type": "OnDuty",
            "time_result": "Normal",
            "source_type": "test",
        }
        result = map_attendance("default", payload)
        expected = datetime.fromtimestamp(milliseconds / 1000, tz=dt_timezone.utc).astimezone(
            timezone.get_current_timezone()
        )
        self.assertEqual(result["userid"], "user-1")
        self.assertEqual(result["record_id"], "record-1")
        self.assertEqual(result["user_check_time"], expected)

    def test_map_attendance_accepts_iso_string(self):
        iso_value = "2025-10-01T15:30:00"
        payload = {
            "userid": "user-2",
            "user_check_time": iso_value,
            "record_id": "record-2",
        }
        result = map_attendance("default", payload)
        expected = timezone.make_aware(datetime.strptime(iso_value, "%Y-%m-%dT%H:%M:%S"))
        self.assertEqual(result["user_check_time"], expected)


class MapDimissionTests(SimpleTestCase):
    def test_map_dimission_extracts_common_field_variants(self):
        info = {
            "userId": "user-1",
            "employeeName": "张三",
            "mobilePhone": "13800001234",
            "jobNo": "J001",
            "mainDeptId": "200",
            "mainDeptName": "研发中心",
            "handoverUserId": "manager-1",
        }
        result = map_dimission("default", info)

        self.assertEqual(result["userid"], "user-1")
        self.assertEqual(result["name"], "张三")
        self.assertEqual(result["mobile"], "13800001234")
        self.assertEqual(result["job_number"], "J001")
        self.assertEqual(result["main_dept_id"], 200)
        self.assertEqual(result["main_dept_name"], "研发中心")
        self.assertEqual(result["handover_userid"], "manager-1")

    def test_map_dimission_falls_back_to_leave_record_and_reason_lists(self):
        info = {
            "userid": "user-2",
            "deptList": [{"deptId": "10"}],
        }
        leave_record = {
            "userName": "李四",
            "mobile": "13900001234",
            "jobNumber": "J002",
            "deptId": "300",
            "deptName": "市场部",
            "voluntaryReasons": ["工作内容调整"],
            "leaveReason": "个人原因",
        }

        result = map_dimission("default", info, leave_record)

        self.assertEqual(result["name"], "李四")
        self.assertEqual(result["mobile"], "13900001234")
        self.assertEqual(result["job_number"], "J002")
        self.assertEqual(result["main_dept_id"], 300)
        self.assertEqual(result["main_dept_name"], "市场部")
        self.assertEqual(result["leave_reason"], "个人原因")
        self.assertEqual(result["voluntary_reasons"], ["工作内容调整"])
        self.assertEqual(result["dept_ids"], [10])
