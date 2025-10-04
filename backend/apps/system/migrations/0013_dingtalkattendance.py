from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("system", "0012_dingtalkconfig_dingtalkdepartment_dingtalksynclog_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="dingtalkconfig",
            name="last_attendance_sync_count",
            field=models.IntegerField(default=0, verbose_name="最近同步考勤数量"),
        ),
        migrations.AddField(
            model_name="dingtalkconfig",
            name="last_attendance_sync_time",
            field=models.DateTimeField(blank=True, null=True, verbose_name="考勤最近同步时间"),
        ),
        migrations.CreateModel(
            name="DingTalkAttendanceRecord",
            fields=[
                ("create_time", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("update_time", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "record_id",
                    models.CharField(max_length=128, primary_key=True, serialize=False, verbose_name="记录ID"),
                ),
                ("userid", models.CharField(max_length=128, verbose_name="用户ID")),
                ("check_type", models.CharField(blank=True, default="", max_length=32, verbose_name="打卡类型")),
                ("time_result", models.CharField(blank=True, default="", max_length=32, verbose_name="结果")),
                ("user_check_time", models.DateTimeField(verbose_name="打卡时间")),
                ("work_date", models.DateField(blank=True, null=True, verbose_name="工作日期")),
                ("source_type", models.CharField(blank=True, default="", max_length=32, verbose_name="来源类型")),
                ("source_info", models.JSONField(blank=True, default=dict, verbose_name="原始数据")),
            ],
            options={
                "verbose_name": "钉钉考勤记录",
                "verbose_name_plural": "钉钉考勤记录",
                "ordering": ("-user_check_time", "userid"),
            },
        ),
    ]
