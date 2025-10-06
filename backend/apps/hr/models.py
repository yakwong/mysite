from __future__ import annotations

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.dingtalk.models import DingTalkDepartment, DingTalkUser
from apps.user.models import User
from utils.models import BaseModel, UuidModel


class Department(UuidModel, BaseModel):
    """人力资源部门"""

    class Status(models.IntegerChoices):
        ACTIVE = 1, "启用"
        INACTIVE = 0, "停用"

    name = models.CharField(max_length=255, verbose_name="部门名称")
    code = models.CharField(max_length=64, unique=True, verbose_name="部门编码")
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级部门",
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        verbose_name="负责人",
    )
    ding_department = models.OneToOneField(
        DingTalkDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_department",
        verbose_name="钉钉部门",
    )
    config_id = models.CharField(max_length=64, blank=True, default="", verbose_name="配置ID")
    description = models.TextField(blank=True, default="", verbose_name="说明")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="附加信息")
    status = models.SmallIntegerField(choices=Status.choices, default=Status.ACTIVE, verbose_name="状态")

    class Meta:
        db_table = "hr_department"
        verbose_name = "人力资源部门"
        verbose_name_plural = verbose_name
        ordering = ("code",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name}({self.code})"


class Employee(UuidModel, BaseModel):
    """员工信息"""

    class EmploymentStatus(models.IntegerChoices):
        PROBATION = 1, "试用"
        FULL_TIME = 2, "在职"
        SUSPENDED = 3, "停薪留职"
        LEFT = 4, "离职"

    class EmploymentType(models.IntegerChoices):
        FULL_TIME = 1, "全职"
        PART_TIME = 2, "兼职"
        INTERN = 3, "实习"
        CONTRACTOR = 4, "外包"

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name="所属部门",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_profile",
        verbose_name="关联用户",
    )
    ding_user = models.OneToOneField(
        DingTalkUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_employee",
        verbose_name="钉钉用户",
    )
    config_id = models.CharField(max_length=64, blank=True, default="", verbose_name="配置ID")
    name = models.CharField(max_length=255, verbose_name="姓名")
    job_number = models.CharField(max_length=64, unique=True, verbose_name="工号")
    email = models.EmailField(blank=True, default="", verbose_name="邮箱")
    phone = models.CharField(max_length=32, blank=True, default="", verbose_name="电话")
    title = models.CharField(max_length=255, blank=True, default="", verbose_name="职位")
    employment_type = models.SmallIntegerField(
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
        verbose_name="雇佣类型",
    )
    employment_status = models.SmallIntegerField(
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.PROBATION,
        verbose_name="雇佣状态",
    )
    hire_date = models.DateField(null=True, blank=True, verbose_name="入职日期")
    regular_date = models.DateField(null=True, blank=True, verbose_name="转正日期")
    separation_date = models.DateField(null=True, blank=True, verbose_name="离职日期")
    base_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="基础工资",
    )
    allowance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="固定补贴",
    )
    metadata = models.JSONField(default=dict, blank=True, verbose_name="附加信息")

    class Meta:
        db_table = "hr_employee"
        verbose_name = "员工信息"
        verbose_name_plural = verbose_name
        ordering = ("job_number",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name}({self.job_number})"


class AttendanceRule(UuidModel, BaseModel):
    """考勤规则"""

    name = models.CharField(max_length=128, unique=True, verbose_name="规则名称")
    description = models.TextField(blank=True, default="", verbose_name="说明")
    workday_start = models.TimeField(verbose_name="工作开始时间")
    workday_end = models.TimeField(verbose_name="工作结束时间")
    allow_late_minutes = models.PositiveIntegerField(default=0, verbose_name="允许迟到分钟数")
    allow_early_minutes = models.PositiveIntegerField(default=0, verbose_name="允许早退分钟数")
    absence_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name="记缺勤阈值",
        help_text="超过该分钟数记为缺勤",
    )
    overtime_start_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="加班判定阈值",
        help_text="超过下班时间多少分钟计为加班",
    )
    weekend_as_workday = models.BooleanField(default=False, verbose_name="周末算工作日")
    custom_workdays = models.JSONField(
        default=list,
        blank=True,
        verbose_name="自定义工作日",
        help_text="例如 [1,2,3,4,5] 表示周一至周五",
    )

    class Meta:
        db_table = "hr_attendance_rule"
        verbose_name = "考勤规则"
        verbose_name_plural = verbose_name
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class AttendanceSummary(UuidModel, BaseModel):
    """员工考勤统计"""

    class Status(models.IntegerChoices):
        DRAFT = 1, "待确认"
        CONFIRMED = 2, "已确认"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_summaries", verbose_name="员工")
    rule = models.ForeignKey(AttendanceRule, on_delete=models.PROTECT, related_name="summaries", verbose_name="规则")
    period_start = models.DateField(verbose_name="统计开始")
    period_end = models.DateField(verbose_name="统计结束")
    work_days = models.PositiveIntegerField(default=0, verbose_name="应出勤天数")
    present_days = models.PositiveIntegerField(default=0, verbose_name="实际出勤天数")
    late_minutes = models.PositiveIntegerField(default=0, verbose_name="迟到分钟数")
    early_leave_minutes = models.PositiveIntegerField(default=0, verbose_name="早退分钟数")
    absence_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="缺勤天数",
    )
    overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="加班小时",
    )
    detail = models.JSONField(default=dict, blank=True, verbose_name="明细")
    status = models.SmallIntegerField(choices=Status.choices, default=Status.DRAFT, verbose_name="状态")

    class Meta:
        db_table = "hr_attendance_summary"
        verbose_name = "考勤统计"
        verbose_name_plural = verbose_name
        ordering = ("-period_start", "employee__job_number")
        constraints = [
            models.UniqueConstraint(
                fields=("employee", "period_start", "period_end"),
                name="uniq_employee_period",
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.employee}-{self.period_start}~{self.period_end}"


class PayrollRule(UuidModel, BaseModel):
    """薪资计算规则"""

    name = models.CharField(max_length=128, unique=True, verbose_name="规则名称")
    description = models.TextField(blank=True, default="", verbose_name="说明")
    overtime_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("1.5"),
        verbose_name="加班倍数",
    )
    late_penalty_per_minute = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="迟到扣款/分钟",
    )
    absence_penalty_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="缺勤扣款/天",
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.1"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        verbose_name="个税比例",
    )
    other_allowance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="额外补贴",
    )

    class Meta:
        db_table = "hr_payroll_rule"
        verbose_name = "薪资规则"
        verbose_name_plural = verbose_name
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class PayrollRecord(UuidModel, BaseModel):
    """薪资发放记录"""

    class Status(models.IntegerChoices):
        DRAFT = 1, "待发放"
        APPROVED = 2, "已确认"
        PAID = 3, "已发放"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payroll_records", verbose_name="员工")
    rule = models.ForeignKey(PayrollRule, on_delete=models.PROTECT, related_name="payroll_records", verbose_name="规则")
    attendance_summary = models.ForeignKey(
        AttendanceSummary,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_records",
        verbose_name="关联考勤",
    )
    period_start = models.DateField(verbose_name="发薪开始")
    period_end = models.DateField(verbose_name="发薪结束")
    gross_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="应发工资",
    )
    deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="扣减合计",
    )
    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="实发工资",
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="个税",
    )
    remark = models.TextField(blank=True, default="", verbose_name="备注")
    detail = models.JSONField(default=dict, blank=True, verbose_name="明细")
    status = models.SmallIntegerField(choices=Status.choices, default=Status.DRAFT, verbose_name="状态")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="发放时间")

    class Meta:
        db_table = "hr_payroll_record"
        verbose_name = "薪资记录"
        verbose_name_plural = verbose_name
        ordering = ("-period_start", "employee__job_number")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.employee}-{self.period_start}"
