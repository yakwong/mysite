from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_alter_user_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="description",
            field=models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name="简介"),
        ),
    ]
