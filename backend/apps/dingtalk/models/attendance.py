from __future__ import annotations

from django.db import models

from utils.models import BaseModel


class DingTalkAttendanceRecord(BaseModel):
    """钉钉考勤记录"""

    record_id = models.CharField(primary_key=True, max_length=128, verbose_name="记录ID")
    config = models.ForeignKey(
        "DingTalkConfig",
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name="所属配置",
        default="default",
    )
    userid = models.CharField(max_length=128, verbose_name="用户ID")
    check_type = models.CharField(max_length=32, blank=True, default="", verbose_name="打卡类型")
    time_result = models.CharField(max_length=32, blank=True, default="", verbose_name="结果")
    user_check_time = models.DateTimeField(verbose_name="打卡时间")
    work_date = models.DateField(null=True, blank=True, verbose_name="工作日期")
    source_type = models.CharField(max_length=32, blank=True, default="", verbose_name="来源类型")
    source_info = models.JSONField(default=dict, blank=True, verbose_name="原始数据")

    class Meta:
        db_table = "dingtalk_attendance_record"
        verbose_name = "钉钉考勤记录"
        verbose_name_plural = verbose_name
        ordering = ("-user_check_time", "userid")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.userid}@{self.user_check_time.isoformat()}"
