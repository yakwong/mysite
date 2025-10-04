from django.db import models
from utils.models import UuidModel, BaseModel


class Role(UuidModel, BaseModel):
    name = models.CharField(max_length=128, verbose_name=("角色名称"), unique=True)
    code = models.CharField(max_length=128, verbose_name=("角色代码"), unique=True)
    status = models.BooleanField(verbose_name=("激活状态"), default=True)
    menu = models.ManyToManyField("system.Menu", verbose_name=("菜单/权限"), blank=True)
    parent = models.ForeignKey("system.Role", on_delete=models.SET_NULL, verbose_name=("父级角色"), null=True, blank=True)

    class Meta:
        verbose_name = "角色表"
        verbose_name_plural = verbose_name
        ordering = ("create_time",)

    def __str__(self):
        return f"{self.name}({self.code})"


class Menu(UuidModel, BaseModel):
    class MenuChoices(models.IntegerChoices):
        DIRECTORY = 0, "Directory"
        MENU = 1, "Menu"
        PERMISSION = 2, "Permission"

    class MethodChoices(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        DELETE = "DELETE", "DELETE"
        PATCH = "PATCH", "PATCH"

    parent = models.ForeignKey("system.Menu", on_delete=models.SET_NULL, verbose_name=("父级菜单"), null=True, blank=True)
    menu_type = models.SmallIntegerField(choices=MenuChoices.choices, default=MenuChoices.DIRECTORY, verbose_name=("菜单类型"))
    name = models.CharField(verbose_name=("标识名称"), max_length=128)
    code = models.CharField(verbose_name=("权限标识"), max_length=128, unique=True, null=True, default=None)
    path = models.CharField(verbose_name=("路由地址"), max_length=255, null=True)
    component = models.CharField(verbose_name=("组件地址"), max_length=255, null=True, blank=True)
    status = models.BooleanField(verbose_name=("激活"), default=True)
    meta = models.OneToOneField(
        "system.MenuMeta",
        on_delete=models.CASCADE,
        verbose_name=("Menu meta"),
        null=True,
    )
    method = models.CharField(choices=MethodChoices.choices, null=True, blank=True, verbose_name=("Method"), max_length=10)
    redirect = models.CharField(verbose_name=("Redirect"), max_length=255, null=True, blank=True, help_text=("Redirect address"))

    def delete(self, using=None, keep_parents=False):
        if self.meta:
            self.meta.delete(using, keep_parents)
        super().delete(using, keep_parents)

    class Meta:
        verbose_name = "菜单/权限表"
        verbose_name_plural = verbose_name
        ordering = ("create_time",)

    def __str__(self):
        return f"{self.meta.title}-{self.get_menu_type_display()}({self.name})"


class MenuMeta(UuidModel, BaseModel):
    title = models.CharField(verbose_name=("Menu title"), max_length=255, null=True, blank=True)
    icon = models.CharField(verbose_name=("Left icon"), max_length=255, null=True, blank=True)
    rank = models.IntegerField(verbose_name=("菜单显示优先级"), default=9999)
    r_svg_name = models.CharField(verbose_name=("Right icon"), max_length=255, null=True, blank=True, help_text=("Additional icon to the right of menu name"))
    is_show_menu = models.BooleanField(verbose_name=("Show menu"), default=True)
    is_show_parent = models.BooleanField(verbose_name=("Show parent menu"), default=False)
    is_keepalive = models.BooleanField(verbose_name=("Keepalive"), default=False, help_text=("When enabled, the entire state of the page is saved, and when refreshed, the state is cleared"))
    frame_url = models.CharField(verbose_name=("Iframe URL"), max_length=255, null=True, blank=True, help_text=("The embedded iframe link address"))
    frame_loading = models.BooleanField(verbose_name=("Iframe loading"), default=False)

    transition_enter = models.CharField(verbose_name=("Enter animation"), max_length=255, null=True, blank=True)
    transition_leave = models.CharField(verbose_name=("Leave animation"), max_length=255, null=True, blank=True)

    is_hidden_tag = models.BooleanField(verbose_name=("Hidden tag"), default=False, help_text=("The current menu name or custom information is prohibited from being added to the TAB"))
    fixed_tag = models.BooleanField(verbose_name=("Fixed tag"), default=False, help_text=("Whether the current menu name is fixed to the TAB and cannot be closed"))
    dynamic_level = models.IntegerField(verbose_name=("Dynamic level"), default=0, help_text=("Maximum number of dynamic routes that can be opened"))

    class Meta:
        verbose_name = "Menu meta"
        verbose_name_plural = verbose_name
        ordering = ("-create_time",)

    def __str__(self):
        return f"{self.title}-{self.description}"


class DeptInfo(UuidModel, BaseModel):
    name = models.CharField(verbose_name=("Department name"), max_length=128)
    code = models.CharField(max_length=128, verbose_name=("Department code"), unique=True)
    type = models.SmallIntegerField(verbose_name=("Department type"), default=0)
    parent = models.ForeignKey("system.DeptInfo", on_delete=models.SET_NULL, verbose_name=("Superior department"), null=True, blank=True, related_query_name="parent_query")
    roles = models.ManyToManyField("system.Role", verbose_name=("Role permission"), blank=True)
    rank = models.IntegerField(verbose_name=("Rank"), default=99)
    auto_bind = models.BooleanField(verbose_name=("Auto bind"), default=False, help_text=("If the value of the registration parameter channel is consistent with the department code, the user is automatically bound to the department"))
    status = models.BooleanField(verbose_name=("Is active"), default=True)

    class Meta:
        verbose_name = "部门表"
        verbose_name_plural = verbose_name
        ordering = (
            "rank",
            "create_time",
        )

    def __str__(self):
        return f"{self.name}({self.pk})"

    # 定义一个方法，获取当前部门以及其所有子部门包括子部门id列表
    def get_child_dept_ids(self):
        dept_ids = [self.pk]
        children = DeptInfo.objects.filter(parent=self)
        for child in children:
            dept_ids.extend(child.get_child_dept_ids())
        return dept_ids


class DingTalkConfig(BaseModel):
    """钉钉配置"""

    DEFAULT_ID = "default"

    id = models.CharField(primary_key=True, max_length=32, default=DEFAULT_ID, editable=False, verbose_name="配置ID")
    app_key = models.CharField(max_length=128, blank=True, default="", verbose_name="App Key")
    app_secret = models.CharField(max_length=256, blank=True, default="", verbose_name="App Secret")
    agent_id = models.CharField(max_length=64, blank=True, default="", verbose_name="Agent ID")
    enabled = models.BooleanField(default=False, verbose_name="是否启用")
    sync_users = models.BooleanField(default=True, verbose_name="同步用户")
    sync_departments = models.BooleanField(default=True, verbose_name="同步部门")
    callback_url = models.CharField(max_length=512, blank=True, default="", verbose_name="回调地址")
    remark = models.TextField(blank=True, default="", verbose_name="备注")

    access_token = models.CharField(max_length=512, blank=True, default="", verbose_name="访问令牌")
    access_token_expires_at = models.DateTimeField(null=True, blank=True, verbose_name="令牌过期时间")

    last_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="最近同步时间")
    last_user_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="用户最近同步时间")
    last_dept_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="部门最近同步时间")
    last_sync_status = models.CharField(max_length=32, blank=True, default="", verbose_name="最近同步状态")
    last_sync_message = models.CharField(max_length=512, blank=True, default="", verbose_name="最近同步信息")
    last_user_sync_count = models.IntegerField(default=0, verbose_name="最近同步用户数量")
    last_dept_sync_count = models.IntegerField(default=0, verbose_name="最近同步部门数量")
    last_attendance_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="考勤最近同步时间")
    last_attendance_sync_count = models.IntegerField(default=0, verbose_name="最近同步考勤数量")

    class Meta:
        verbose_name = "钉钉配置"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.DEFAULT_ID
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(id=cls.DEFAULT_ID)
        return obj


class DingTalkSyncLog(UuidModel, BaseModel):
    """钉钉同步日志"""

    class Operation(models.TextChoices):
        TEST_CONNECTION = "test_connection", "测试连接"
        SYNC_DEPARTMENTS = "sync_departments", "同步部门"
        SYNC_USERS = "sync_users", "同步用户"
        FULL_SYNC = "full_sync", "全量同步"
        SYNC_ATTENDANCE = "sync_attendance", "同步考勤"

    class Status(models.TextChoices):
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"

    operation = models.CharField(max_length=32, choices=Operation.choices, verbose_name="操作类型")
    status = models.CharField(max_length=16, choices=Status.choices, verbose_name="状态")
    message = models.CharField(max_length=512, blank=True, default="", verbose_name="消息")
    detail = models.TextField(blank=True, default="", verbose_name="详细信息")
    stats = models.JSONField(default=dict, blank=True, verbose_name="统计数据")

    class Meta:
        verbose_name = "钉钉同步日志"
        verbose_name_plural = verbose_name
        ordering = ("-create_time",)

    def __str__(self):
        return f"{self.get_operation_display()}-{self.get_status_display()}"


class DingTalkDepartment(BaseModel):
    """钉钉部门快照"""

    dept_id = models.BigIntegerField(primary_key=True, verbose_name="部门ID")
    name = models.CharField(max_length=255, verbose_name="部门名称")
    parent_id = models.BigIntegerField(null=True, blank=True, verbose_name="父级部门ID")
    order = models.BigIntegerField(null=True, blank=True, verbose_name="排序")
    leader_userid = models.CharField(max_length=128, blank=True, default="", verbose_name="负责人")
    dept_type = models.CharField(max_length=64, blank=True, default="", verbose_name="部门类型")
    source_info = models.JSONField(default=dict, blank=True, verbose_name="原始数据")

    class Meta:
        verbose_name = "钉钉部门"
        verbose_name_plural = verbose_name
        ordering = ("dept_id",)

    def __str__(self):
        return f"{self.name}({self.dept_id})"


class DingTalkUser(BaseModel):
    """钉钉用户快照"""

    userid = models.CharField(primary_key=True, max_length=128, verbose_name="用户ID")
    name = models.CharField(max_length=255, blank=True, default="", verbose_name="姓名")
    mobile = models.CharField(max_length=64, blank=True, default="", verbose_name="手机号")
    email = models.CharField(max_length=255, blank=True, default="", verbose_name="邮箱")
    active = models.BooleanField(default=True, verbose_name="是否激活")
    job_number = models.CharField(max_length=128, blank=True, default="", verbose_name="工号")
    title = models.CharField(max_length=255, blank=True, default="", verbose_name="职位")
    dept_ids = models.JSONField(default=list, blank=True, verbose_name="所属部门ID列表")
    unionid = models.CharField(max_length=255, blank=True, default="", verbose_name="UnionID")
    remark = models.CharField(max_length=255, blank=True, default="", verbose_name="备注")
    source_info = models.JSONField(default=dict, blank=True, verbose_name="原始数据")

    class Meta:
        verbose_name = "钉钉用户"
        verbose_name_plural = verbose_name
        ordering = ("userid",)

    def __str__(self):
        return f"{self.name}({self.userid})"


class DingTalkAttendanceRecord(BaseModel):
    """钉钉考勤记录"""

    record_id = models.CharField(primary_key=True, max_length=128, verbose_name="记录ID")
    userid = models.CharField(max_length=128, verbose_name="用户ID")
    check_type = models.CharField(max_length=32, blank=True, default="", verbose_name="打卡类型")
    time_result = models.CharField(max_length=32, blank=True, default="", verbose_name="结果")
    user_check_time = models.DateTimeField(verbose_name="打卡时间")
    work_date = models.DateField(null=True, blank=True, verbose_name="工作日期")
    source_type = models.CharField(max_length=32, blank=True, default="", verbose_name="来源类型")
    source_info = models.JSONField(default=dict, blank=True, verbose_name="原始数据")

    class Meta:
        verbose_name = "钉钉考勤记录"
        verbose_name_plural = verbose_name
        ordering = ("-user_check_time", "userid")

    def __str__(self):
        return f"{self.userid}@{self.user_check_time.isoformat()}"
