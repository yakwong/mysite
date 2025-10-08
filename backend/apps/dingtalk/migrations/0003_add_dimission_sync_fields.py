from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dingtalk", "0002_dingtalkdimissionuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="dingtalkconfig",
            name="last_dimission_sync_count",
            field=models.IntegerField(default=0, verbose_name="最近同步离职人员数量"),
        ),
        migrations.AddField(
            model_name="dingtalkconfig",
            name="last_dimission_sync_time",
            field=models.DateTimeField(blank=True, null=True, verbose_name="离职人员最近同步时间"),
        ),
    ]

