from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("dingtalk", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DingTalkDimissionUser",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="ID")),
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("userid", models.CharField(max_length=128, verbose_name="用户ID")),
                ("name", models.CharField(blank=True, default="", max_length=255, verbose_name="姓名")),
                ("mobile", models.CharField(blank=True, default="", max_length=64, verbose_name="手机号")),
                ("job_number", models.CharField(blank=True, default="", max_length=128, verbose_name="工号")),
                ("main_dept_id", models.BigIntegerField(blank=True, null=True, verbose_name="主部门ID")),
                ("main_dept_name", models.CharField(blank=True, default="", max_length=255, verbose_name="主部门名称")),
                ("handover_userid", models.CharField(blank=True, default="", max_length=128, verbose_name="交接人用户ID")),
                ("last_work_day", models.DateField(blank=True, null=True, verbose_name="最后工作日")),
                ("leave_time", models.DateTimeField(blank=True, null=True, verbose_name="离职时间")),
                ("leave_reason", models.CharField(blank=True, default="", max_length=255, verbose_name="离职原因")),
                ("reason_type", models.IntegerField(blank=True, null=True, verbose_name="原因类型")),
                ("reason_memo", models.CharField(blank=True, default="", max_length=1024, verbose_name="离职备注")),
                ("pre_status", models.IntegerField(blank=True, null=True, verbose_name="离职前状态")),
                ("status", models.IntegerField(blank=True, null=True, verbose_name="离职状态")),
                ("voluntary_reasons", models.JSONField(blank=True, default=list, verbose_name="主动离职原因")),
                ("passive_reasons", models.JSONField(blank=True, default=list, verbose_name="被动离职原因")),
                ("dept_ids", models.JSONField(blank=True, default=list, verbose_name="历史部门列表")),
                ("source_info", models.JSONField(blank=True, default=dict, verbose_name="原始数据")),
                (
                    "config",
                    models.ForeignKey(
                        default="default",
                        on_delete=models.deletion.CASCADE,
                        related_name="dimission_users",
                        to="dingtalk.dingtalkconfig",
                        verbose_name="所属配置",
                    ),
                ),
            ],
            options={
                "verbose_name": "钉钉离职员工",
                "verbose_name_plural": "钉钉离职员工",
                "db_table": "dingtalk_dimission_user",
                "ordering": ("-leave_time", "userid"),
                "unique_together": {("config", "userid")},
            },
        ),
    ]

