from datetime import datetime, timezone as dt_timezone

from django.test import SimpleTestCase
from django.utils import timezone

from apps.dingtalk.services.mappers import map_attendance


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
