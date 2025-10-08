from django.db import migrations


def create_dingtalk_menu(apps, schema_editor):
    Menu = apps.get_model("system", "Menu")
    MenuMeta = apps.get_model("system", "MenuMeta")
    Role = apps.get_model("system", "Role")

    if Menu.objects.filter(path="/dingtalk").exists():
        return

    meta_defaults = {
        "r_svg_name": "",
        "is_show_menu": True,
        "is_show_parent": False,
        "is_keepalive": False,
        "frame_loading": False,
        "is_hidden_tag": False,
        "fixed_tag": False,
        "dynamic_level": 0,
    }

    root_meta = MenuMeta.objects.create(
        title="钉钉中心",
        icon="ri:dingding-line",
        rank=3,
        **meta_defaults,
    )
    menu_type_menu = getattr(getattr(Menu, "MenuChoices", None), "MENU", 1)

    root_menu = Menu.objects.create(
        parent=None,
        menu_type=menu_type_menu,
        name="dingtalk-center",
        path="/dingtalk",
        component=None,
        status=True,
        meta=root_meta,
        redirect="/dingtalk/dashboard",
    )

    child_configs = [
        ("dingtalk-dashboard", "/dingtalk/dashboard", "modules/dingtalk/views/Dashboard", "总览"),
        ("dingtalk-logs", "/dingtalk/logs", "modules/dingtalk/views/Logs", "同步日志"),
        ("dingtalk-departments", "/dingtalk/departments", "modules/dingtalk/views/Departments", "部门数据"),
        ("dingtalk-users", "/dingtalk/users", "modules/dingtalk/views/Users", "人员数据"),
        ("dingtalk-attendance", "/dingtalk/attendance", "modules/dingtalk/views/Attendance", "考勤记录"),
        ("dingtalk-settings", "/dingtalk/settings", "modules/dingtalk/views/Settings", "高级设置"),
    ]

    child_menus = []
    for order, (name, path, component, title) in enumerate(child_configs, start=1):
        child_meta = MenuMeta.objects.create(title=title, icon="", rank=order, **meta_defaults)
        menu = Menu.objects.create(
            parent=root_menu,
            menu_type=menu_type_menu,
            name=name,
            path=path,
            component=component,
            status=True,
            meta=child_meta,
            redirect=None,
        )
        child_menus.append(menu)

    roles = Role.objects.filter(code__in=["superadmin", "admins", "useradmin", "preview"])
    for role in roles:
        role.menu.add(root_menu, *child_menus)


def remove_dingtalk_menu(apps, schema_editor):
    Menu = apps.get_model("system", "Menu")
    menus = Menu.objects.filter(path__startswith="/dingtalk").order_by("path")
    for menu in menus:
        menu.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0014_remove_dingtalk_models"),
    ]

    operations = [
        migrations.RunPython(create_dingtalk_menu, remove_dingtalk_menu),
    ]
