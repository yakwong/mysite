from __future__ import annotations

import uuid

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


SYNC_OPERATION_CHOICES = [
    ("test_connection", "TEST_CONNECTION"),
    ("sync_departments", "SYNC_DEPARTMENTS"),
    ("sync_users", "SYNC_USERS"),
    ("sync_attendance", "SYNC_ATTENDANCE"),
    ("full_sync", "FULL_SYNC"),
]

SYNC_STATUS_CHOICES = [
    ("success", "SUCCESS"),
    ("failed", "FAILED"),
    ("pending", "PENDING"),
]


def copy_legacy_tables(apps, schema_editor):
    """从 apps.system 原有表迁移数据到新表"""

    SystemConfig = apps.get_model("system", "DingTalkConfig")
    SystemDepartment = apps.get_model("system", "DingTalkDepartment")
    SystemUser = apps.get_model("system", "DingTalkUser")
    SystemAttendance = apps.get_model("system", "DingTalkAttendanceRecord")
    SystemLog = apps.get_model("system", "DingTalkSyncLog")

    NewConfig = apps.get_model("dingtalk", "DingTalkConfig")
    NewDepartment = apps.get_model("dingtalk", "DingTalkDepartment")
    NewUser = apps.get_model("dingtalk", "DingTalkUser")
    NewAttendance = apps.get_model("dingtalk", "DingTalkAttendanceRecord")
    NewLog = apps.get_model("dingtalk", "DingTalkSyncLog")

    def resolve_config(source_info):
        if isinstance(source_info, dict):
            return config_map.get(source_info.get("config_id", "default"), default_config)
        return default_config

    for cfg in SystemConfig.objects.all():
        NewConfig.objects.update_or_create(
            id=cfg.id,
            defaults={
                "name": cfg.remark or ("默认钉钉配置" if cfg.id == "default" else cfg.id),
                "tenant_id": "",
                "app_key": cfg.app_key,
                "app_secret": cfg.app_secret,
                "agent_id": cfg.agent_id,
                "enabled": cfg.enabled,
                "sync_users": cfg.sync_users,
                "sync_departments": cfg.sync_departments,
                "sync_attendance": False,
                "callback_url": cfg.callback_url,
                "callback_token": "",
                "callback_aes_key": "",
                "remark": cfg.remark,
                "access_token": cfg.access_token,
                "access_token_expires_at": cfg.access_token_expires_at,
                "last_sync_time": cfg.last_sync_time,
                "last_sync_status": cfg.last_sync_status,
                "last_sync_message": cfg.last_sync_message,
                "last_user_sync_time": cfg.last_user_sync_time,
                "last_dept_sync_time": cfg.last_dept_sync_time,
                "last_attendance_sync_time": cfg.last_attendance_sync_time,
                "last_user_sync_count": cfg.last_user_sync_count,
                "last_dept_sync_count": cfg.last_dept_sync_count,
                "last_attendance_sync_count": cfg.last_attendance_sync_count,
                "schedule": cfg.schedule if hasattr(cfg, "schedule") else {},
                "created_by": "",
                "updated_by": "",
                "create_time": cfg.create_time or timezone.now(),
                "update_time": cfg.update_time or timezone.now(),
            },
        )

    config_map = {item.id: item for item in NewConfig.objects.all()}
    default_config = config_map.get("default") or next(iter(config_map.values()), None)

    for dept in SystemDepartment.objects.all():
        NewDepartment.objects.update_or_create(
            dept_id=dept.dept_id,
            defaults={
                "config": resolve_config(getattr(dept, "source_info", {})),
                "name": dept.name,
                "parent_id": dept.parent_id,
                "order": dept.order,
                "leader_userid": dept.leader_userid,
                "dept_type": getattr(dept, "dept_type", ""),
                "source_info": getattr(dept, "source_info", {}) or {},
                "create_time": dept.create_time or timezone.now(),
                "update_time": dept.update_time or timezone.now(),
            },
        )

    for user in SystemUser.objects.all():
        NewUser.objects.update_or_create(
            userid=user.userid,
            defaults={
                "config": resolve_config(getattr(user, "source_info", {})),
                "name": user.name,
                "mobile": user.mobile,
                "email": user.email,
                "active": user.active,
                "job_number": user.job_number,
                "title": user.title,
                "dept_ids": user.dept_ids or [],
                "unionid": user.unionid,
                "remark": user.remark,
                "source_info": getattr(user, "source_info", {}) or {},
                "create_time": user.create_time or timezone.now(),
                "update_time": user.update_time or timezone.now(),
            },
        )

    for record in SystemAttendance.objects.all():
        NewAttendance.objects.update_or_create(
            record_id=record.record_id,
            defaults={
                "config": resolve_config(getattr(record, "source_info", {})),
                "userid": record.userid,
                "check_type": record.check_type,
                "time_result": record.time_result,
                "user_check_time": record.user_check_time,
                "work_date": record.work_date,
                "source_type": record.source_type,
                "source_info": getattr(record, "source_info", {}) or {},
                "create_time": record.create_time or timezone.now(),
                "update_time": record.update_time or timezone.now(),
            },
        )

    for log in SystemLog.objects.all():
        NewLog.objects.update_or_create(
            id=log.id,
            defaults={
                "config": default_config,
                "operation": log.operation,
                "status": log.status,
                "level": "info",
                "message": log.message,
                "detail": log.detail,
                "stats": getattr(log, "stats", {}) or {},
                "retry_count": 0,
                "next_retry_at": None,
                "create_time": log.create_time or timezone.now(),
                "update_time": log.update_time or timezone.now(),
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("system", "0013_dingtalkattendance"),
    ]

    operations = [
        migrations.CreateModel(
            name="DingTalkConfig",
            fields=[
                ("id", models.CharField(default="default", max_length=32, primary_key=True, serialize=False, verbose_name="配置ID")),
                ("name", models.CharField(default="默认钉钉配置", max_length=128, verbose_name="配置名称")),
                ("tenant_id", models.CharField(blank=True, default="", max_length=128, verbose_name="租户ID")),
                ("app_key", models.CharField(blank=True, default="", max_length=128, verbose_name="App Key")),
                ("app_secret", models.CharField(blank=True, default="", max_length=256, verbose_name="App Secret")),
                ("agent_id", models.CharField(blank=True, default="", max_length=64, verbose_name="Agent ID")),
                ("enabled", models.BooleanField(default=False, verbose_name="是否启用")),
                ("sync_users", models.BooleanField(default=True, verbose_name="同步用户")),
                ("sync_departments", models.BooleanField(default=True, verbose_name="同步部门")),
                ("sync_attendance", models.BooleanField(default=False, verbose_name="同步考勤")),
                ("callback_url", models.CharField(blank=True, default="", max_length=512, verbose_name="回调地址")),
                ("callback_token", models.CharField(blank=True, default="", max_length=128, verbose_name="回调Token")),
                ("callback_aes_key", models.CharField(blank=True, default="", max_length=128, verbose_name="回调AES Key")),
                ("remark", models.TextField(blank=True, default="", verbose_name="备注")),
                ("access_token", models.CharField(blank=True, default="", max_length=512, verbose_name="访问令牌")),
                ("access_token_expires_at", models.DateTimeField(blank=True, null=True, verbose_name="令牌过期时间")),
                ("last_sync_time", models.DateTimeField(blank=True, null=True, verbose_name="最近同步时间")),
                ("last_sync_status", models.CharField(blank=True, default="", max_length=32, verbose_name="最近同步状态")),
                ("last_sync_message", models.CharField(blank=True, default="", max_length=512, verbose_name="最近同步信息")),
                ("last_user_sync_time", models.DateTimeField(blank=True, null=True, verbose_name="用户最近同步时间")),
                ("last_dept_sync_time", models.DateTimeField(blank=True, null=True, verbose_name="部门最近同步时间")),
                ("last_attendance_sync_time", models.DateTimeField(blank=True, null=True, verbose_name="考勤最近同步时间")),
                ("last_user_sync_count", models.IntegerField(default=0, verbose_name="最近同步用户数量")),
                ("last_dept_sync_count", models.IntegerField(default=0, verbose_name="最近同步部门数量")),
                ("last_attendance_sync_count", models.IntegerField(default=0, verbose_name="最近同步考勤数量")),
                ("schedule", models.JSONField(blank=True, default=dict, verbose_name="计划任务配置")),
                ("created_by", models.CharField(blank=True, default="", max_length=128, verbose_name="创建人")),
                ("updated_by", models.CharField(blank=True, default="", max_length=128, verbose_name="最后修改人")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "db_table": "dingtalk_config",
                "verbose_name": "钉钉配置",
                "verbose_name_plural": "钉钉配置",
            },
        ),
        migrations.CreateModel(
            name="DingTalkDepartment",
            fields=[
                ("dept_id", models.BigIntegerField(primary_key=True, serialize=False, verbose_name="部门ID")),
                ("name", models.CharField(max_length=255, verbose_name="部门名称")),
                ("parent_id", models.BigIntegerField(blank=True, null=True, verbose_name="父级部门ID")),
                ("order", models.BigIntegerField(blank=True, null=True, verbose_name="排序")),
                ("leader_userid", models.CharField(blank=True, default="", max_length=128, verbose_name="负责人")),
                ("dept_type", models.CharField(blank=True, default="", max_length=64, verbose_name="部门类型")),
                ("source_info", models.JSONField(blank=True, default=dict, verbose_name="原始数据")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(
                        default="default",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="departments",
                        to="dingtalk.dingtalkconfig",
                        verbose_name="所属配置",
                    ),
                ),
            ],
            options={
                "ordering": ("dept_id",),
                "db_table": "dingtalk_department",
                "verbose_name": "钉钉部门",
                "verbose_name_plural": "钉钉部门",
            },
        ),
        migrations.CreateModel(
            name="DingTalkUser",
            fields=[
                ("userid", models.CharField(max_length=128, primary_key=True, serialize=False, verbose_name="用户ID")),
                ("name", models.CharField(blank=True, default="", max_length=255, verbose_name="姓名")),
                ("mobile", models.CharField(blank=True, default="", max_length=64, verbose_name="手机号")),
                ("email", models.CharField(blank=True, default="", max_length=255, verbose_name="邮箱")),
                ("active", models.BooleanField(default=True, verbose_name="是否激活")),
                ("job_number", models.CharField(blank=True, default="", max_length=128, verbose_name="工号")),
                ("title", models.CharField(blank=True, default="", max_length=255, verbose_name="职位")),
                ("dept_ids", models.JSONField(blank=True, default=list, verbose_name="所属部门ID列表")),
                ("unionid", models.CharField(blank=True, default="", max_length=255, verbose_name="UnionID")),
                ("remark", models.CharField(blank=True, default="", max_length=255, verbose_name="备注")),
                ("source_info", models.JSONField(blank=True, default=dict, verbose_name="原始数据")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(
                        default="default",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="users",
                        to="dingtalk.dingtalkconfig",
                        verbose_name="所属配置",
                    ),
                ),
            ],
            options={
                "ordering": ("userid",),
                "db_table": "dingtalk_user",
                "verbose_name": "钉钉用户",
                "verbose_name_plural": "钉钉用户",
            },
        ),
        migrations.CreateModel(
            name="DingTalkAttendanceRecord",
            fields=[
                ("record_id", models.CharField(max_length=128, primary_key=True, serialize=False, verbose_name="记录ID")),
                ("userid", models.CharField(max_length=128, verbose_name="用户ID")),
                ("check_type", models.CharField(blank=True, default="", max_length=32, verbose_name="打卡类型")),
                ("time_result", models.CharField(blank=True, default="", max_length=32, verbose_name="结果")),
                ("user_check_time", models.DateTimeField(verbose_name="打卡时间")),
                ("work_date", models.DateField(blank=True, null=True, verbose_name="工作日期")),
                ("source_type", models.CharField(blank=True, default="", max_length=32, verbose_name="来源类型")),
                ("source_info", models.JSONField(blank=True, default=dict, verbose_name="原始数据")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(
                        default="default",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_records",
                        to="dingtalk.dingtalkconfig",
                        verbose_name="所属配置",
                    ),
                ),
            ],
            options={
                "ordering": ("-user_check_time", "userid"),
                "db_table": "dingtalk_attendance_record",
                "verbose_name": "钉钉考勤记录",
                "verbose_name_plural": "钉钉考勤记录",
            },
        ),
        migrations.CreateModel(
            name="DingTalkSyncLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(choices=[("info", "信息"), ("warning", "警告"), ("error", "错误")], default="info", max_length=16, verbose_name="级别")),
                ("operation", models.CharField(choices=SYNC_OPERATION_CHOICES, max_length=32, verbose_name="操作类型")),
                ("status", models.CharField(choices=SYNC_STATUS_CHOICES, max_length=16, verbose_name="状态")),
                ("message", models.CharField(blank=True, default="", max_length=512, verbose_name="消息")),
                ("detail", models.TextField(blank=True, default="", verbose_name="详细信息")),
                ("stats", models.JSONField(blank=True, default=dict, verbose_name="统计数据")),
                ("retry_count", models.PositiveIntegerField(default=0, verbose_name="重试次数")),
                ("next_retry_at", models.DateTimeField(blank=True, null=True, verbose_name="下次重试时间")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sync_logs",
                        to="dingtalk.dingtalkconfig",
                        verbose_name="所属配置",
                    ),
                ),
            ],
            options={
                "ordering": ("-create_time",),
                "db_table": "dingtalk_sync_log",
                "verbose_name": "钉钉同步日志",
                "verbose_name_plural": "钉钉同步日志",
            },
        ),
        migrations.CreateModel(
            name="SyncCursor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cursor_type", models.CharField(choices=[("department", "部门"), ("user", "用户"), ("attendance", "考勤")], max_length=16)),
                ("value", models.CharField(blank=True, default="", max_length=255)),
                ("extra", models.JSONField(blank=True, default=dict)),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sync_cursors", to="dingtalk.dingtalkconfig"),
                ),
            ],
            options={
                "db_table": "dingtalk_sync_cursor",
                "unique_together": {("config", "cursor_type")},
                "verbose_name": "钉钉同步游标",
                "verbose_name_plural": "钉钉同步游标",
            },
        ),
        migrations.CreateModel(
            name="DeptBinding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name="ID")),
                ("local_dept_code", models.CharField(max_length=128, verbose_name="本地部门标识")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="dept_bindings", to="dingtalk.dingtalkconfig"),
                ),
                (
                    "dingtalk_dept",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bindings", to="dingtalk.dingtalkdepartment"),
                ),
            ],
            options={
                "db_table": "dingtalk_dept_binding",
                "unique_together": {("config", "dingtalk_dept", "local_dept_code")},
                "verbose_name": "钉钉部门绑定",
                "verbose_name_plural": "钉钉部门绑定",
            },
        ),
        migrations.CreateModel(
            name="UserBinding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name="ID")),
                ("local_user_id", models.CharField(max_length=128, verbose_name="本地用户标识")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_bindings", to="dingtalk.dingtalkconfig"),
                ),
                (
                    "dingtalk_user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bindings", to="dingtalk.dingtalkuser"),
                ),
            ],
            options={
                "db_table": "dingtalk_user_binding",
                "unique_together": {("config", "dingtalk_user", "local_user_id")},
                "verbose_name": "钉钉用户绑定",
                "verbose_name_plural": "钉钉用户绑定",
            },
        ),
        migrations.RunPython(copy_legacy_tables, noop_reverse),
    ]
