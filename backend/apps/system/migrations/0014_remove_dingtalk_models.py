from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0013_dingtalkattendance"),
        ("dingtalk", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("DROP TABLE IF EXISTS system_dingtalkattendancerecord"),
                migrations.RunSQL("DROP TABLE IF EXISTS system_dingtalkuser"),
                migrations.RunSQL("DROP TABLE IF EXISTS system_dingtalkdepartment"),
                migrations.RunSQL("DROP TABLE IF EXISTS system_dingtalksynclog"),
                migrations.RunSQL("DROP TABLE IF EXISTS system_dingtalkconfig"),
            ],
            state_operations=[
                migrations.DeleteModel(name="DingTalkAttendanceRecord"),
                migrations.DeleteModel(name="DingTalkUser"),
                migrations.DeleteModel(name="DingTalkDepartment"),
                migrations.DeleteModel(name="DingTalkSyncLog"),
                migrations.DeleteModel(name="DingTalkConfig"),
            ],
        ),
    ]
