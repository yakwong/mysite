from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.dingtalk.models import DingTalkConfig
from apps.dingtalk.services.client import DingTalkClient
from apps.dingtalk.services.exceptions import DingTalkAPIError


class Command(BaseCommand):
    help = "调试钉钉在职/离职人员接口，直接打印 API 返回结果"

    def add_arguments(self, parser):
        parser.add_argument("--config-id", default=DingTalkConfig.DEFAULT_ID, help="钉钉配置 ID，默认 default")
        parser.add_argument("--max-results", type=int, default=50, help="离职人员列表每次拉取数量 (1-100)")
        parser.add_argument(
            "--dimission-user",
            nargs="*",
            help="指定一组 userId，仅调试这些离职员工详情；默认读取列表接口返回的全部用户",
        )
        parser.add_argument(
            "--dump-active",
            action="store_true",
            help="附加输出在职员工示例（依赖部门同步结果，仅用于验证接口连通性）",
        )
        parser.add_argument(
            "--pretty",
            action="store_true",
            help="使用 JSON 格式化打印返回数据",
        )
        parser.add_argument(
            "--start",
            help="离职记录开始时间，格式 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，默认一年内",
        )
        parser.add_argument(
            "--end",
            help="离职记录结束时间，格式同上，默认当前时间",
        )

    def handle(self, *args, **options):
        config_id = options["config_id"]
        max_results = options["max_results"]
        specified_userids = options.get("dimission_user") or []
        pretty = options["pretty"]
        start_option = options.get("start")
        end_option = options.get("end")

        config = DingTalkConfig.load(config_id)
        if not config.app_key or not config.app_secret:
            raise CommandError(f"配置 {config_id} 未填充 app_key/app_secret，无法访问钉钉接口")

        client = DingTalkClient(config)

        def dump(title: str, payload: Any):
            data = json.dumps(payload, ensure_ascii=False, indent=2) if pretty else payload
            self.stdout.write(f"\n=== {title} ===")
            self.stdout.write(str(data))

        try:
            token = client.get_access_token(force_refresh=True)
        except Exception as exc:  # pragma: no cover - 真实接口异常
            raise CommandError(f"获取 accessToken 失败：{exc}") from exc

        self.stdout.write(f"accessToken 获取成功（长度 {len(token)}）")

        try:
            dimission_ids = client.list_dimission_userids(max_results=max_results)
        except DingTalkAPIError as exc:
            raise CommandError(f"拉取离职员工 userId 失败：{exc}") from exc
        except Exception as exc:  # pragma: no cover - 网络等其他异常
            raise CommandError(f"拉取离职员工 userId 时发生未知错误：{exc}") from exc

        dump("离职人员 userId 列表", dimission_ids or "<空>")

        target_userids = specified_userids or dimission_ids
        if target_userids:
            try:
                dimission_infos = client.list_dimission_infos(target_userids)
            except DingTalkAPIError as exc:
                raise CommandError(f"批量查询离职详情失败：{exc}") from exc
            dump("离职人员详情", dimission_infos or "<空>")
        else:
            self.stdout.write("未获取到离职 userId，跳过详情调试")

        try:
            start_dt = None
            end_dt = None
            if start_option:
                try:
                    start_dt = datetime.fromisoformat(start_option)
                except ValueError:
                    try:
                        start_dt = datetime.strptime(start_option, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        start_dt = datetime.strptime(start_option, "%Y-%m-%d")
                if timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt)
            if end_option:
                try:
                    end_dt = datetime.fromisoformat(end_option)
                except ValueError:
                    try:
                        end_dt = datetime.strptime(end_option, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        end_dt = datetime.strptime(end_option, "%Y-%m-%d")
                if timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt)
            dimission_records = client.list_dimission_records(
                max_results=max_results,
                start_time=start_dt,
                end_time=end_dt,
            )
            dump("离职记录（近一年）", dimission_records or "<空>")
        except DingTalkAPIError as exc:
            self.stderr.write(self.style.WARNING(f"离职记录接口调用失败：{exc}"))
        except Exception as exc:  # pragma: no cover - 网络等其他异常
            self.stderr.write(self.style.WARNING(f"离职记录接口调用异常：{exc}"))

        if options["dump_active"]:
            self.stdout.write("\n尝试拉取在职员工示例...")
            try:
                dept_ids = client.list_departments(root_dept_id=1)
                first_dept = dept_ids[0].get("dept_id") if dept_ids else 1
                users = client.list_users_by_dept(first_dept)
                dump("示例部门", dept_ids[0] if dept_ids else "<空>")
                dump("示例部门成员", users[:5])
            except DingTalkAPIError as exc:
                self.stderr.write(self.style.WARNING(f"在职人员接口调用失败：{exc}"))
            except Exception as exc:  # pragma: no cover - 网络等其他异常
                self.stderr.write(self.style.WARNING(f"在职人员接口调用异常：{exc}"))

        self.stdout.write(self.style.SUCCESS("钉钉接口调试命令执行完毕"))
