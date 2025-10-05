from __future__ import annotations

from datetime import datetime

from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from apps.dingtalk.constants import SyncOperation
from apps.dingtalk.models import DingTalkConfig
from apps.dingtalk.services import SyncService


class Command(BaseCommand):
    help = "触发钉钉同步任务"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("operation", choices=[item.value for item in SyncOperation])
        parser.add_argument("--config", dest="config_id", default=DingTalkConfig.DEFAULT_ID)
        parser.add_argument("--mode", dest="mode", choices=["full", "incremental"], default="full")
        parser.add_argument("--start")
        parser.add_argument("--end")

    def handle(self, *args, **options):
        operation = SyncOperation(options["operation"])
        config = DingTalkConfig.load(options["config_id"])
        service = SyncService(config)
        mode = options["mode"]
        start_option = options.get("start")
        end_option = options.get("end")

        if start_option:
            start = timezone.make_aware(datetime.fromisoformat(start_option))
        else:
            start = None
        if end_option:
            end = timezone.make_aware(datetime.fromisoformat(end_option))
        else:
            end = None

        if operation == SyncOperation.TEST_CONNECTION:
            result = service.test_connection()
        elif operation == SyncOperation.SYNC_DEPARTMENTS:
            result = service.sync_departments(mode=mode)
        elif operation == SyncOperation.SYNC_USERS:
            result = service.sync_users(mode=mode)
        elif operation == SyncOperation.SYNC_ATTENDANCE:
            if not start or not end:
                raise ValueError("SYNC_ATTENDANCE 需要提供 --start 与 --end 参数")
            result = service.sync_attendance(start, end, mode=mode)
        elif operation == SyncOperation.FULL_SYNC:
            result = service.full_sync()
        else:  # pragma: no cover - 不会到达
            raise ValueError("未知操作")

        self.stdout.write(self.style.SUCCESS(f"同步完成: {result}"))
