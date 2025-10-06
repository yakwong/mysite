from __future__ import annotations

from django.db import migrations


def create_hr_menu(apps, schema_editor):  # noqa: D401 - data migration
    Menu = apps.get_model("system", "Menu")
    MenuMeta = apps.get_model("system", "MenuMeta")
    Role = apps.get_model("system", "Role")

    def upsert_menu(
        *,
        name: str,
        title: str,
        path: str,
        component: str | None,
        icon: str,
        rank: int,
        parent: Menu | None,
    ) -> Menu:
        menu = Menu.objects.filter(path=path).first()
        if menu:
            meta = menu.meta
            if meta:
                changed = False
                if meta.title != title:
                    meta.title = title
                    changed = True
                if meta.icon != icon:
                    meta.icon = icon
                    changed = True
                if meta.rank != rank:
                    meta.rank = rank
                    changed = True
                if changed:
                    meta.save(update_fields=["title", "icon", "rank", "update_time"])
            else:
                meta = MenuMeta.objects.create(
                    title=title,
                    icon=icon,
                    rank=rank,
                    is_show_menu=True,
                    is_show_parent=False,
                )
                menu.meta = meta
                menu.save(update_fields=["meta", "update_time"])
            update_fields: list[str] = []
            if menu.name != name:
                menu.name = name
                update_fields.append("name")
            if menu.component != component:
                menu.component = component
                update_fields.append("component")
            if menu.parent_id != (parent.id if parent else None):
                menu.parent = parent
                update_fields.append("parent")
            if menu.menu_type != 1:
                menu.menu_type = 1
                update_fields.append("menu_type")
            if not menu.status:
                menu.status = True
                update_fields.append("status")
            if update_fields:
                menu.save(update_fields=update_fields + ["update_time"])
            return menu

        meta = MenuMeta.objects.create(
            title=title,
            icon=icon,
            rank=rank,
            is_show_menu=True,
            is_show_parent=False,
        )
        menu = Menu.objects.create(
            name=name,
            path=path,
            component=component,
            menu_type=1,
            status=True,
            parent=parent,
            meta=meta,
        )
        return menu

    parent_menu = upsert_menu(
        name="人力资源",
        title="人力资源",
        path="/hr",
        component=None,
        icon="ri:team-line",
        rank=40,
        parent=None,
    )

    child_specs = [
        ("部门管理", "/hr/departments", "/hr/departments/index", "ep:office-building", 41),
        ("员工管理", "/hr/employees", "/hr/employees/index", "ep:user", 42),
        ("考勤规则", "/hr/attendance/rules", "/hr/attendance/rules/index", "ep:calendar", 43),
        ("考勤统计", "/hr/attendance/summary", "/hr/attendance/summary/index", "ep:trend-charts", 44),
        ("薪资规则", "/hr/payroll/rules", "/hr/payroll/rules/index", "ep:coin", 45),
        ("薪资发放", "/hr/payroll/records", "/hr/payroll/records/index", "ep:document", 46),
    ]

    menus = [parent_menu]
    for title, path, component, icon, rank in child_specs:
        menu = upsert_menu(
            name=title,
            title=title,
            path=path,
            component=component,
            icon=icon,
            rank=rank,
            parent=parent_menu,
        )
        menus.append(menu)

    role = Role.objects.filter(code="superadmin").first()
    if role:
        role.menu.add(*menus)


def remove_hr_menu(apps, schema_editor):  # noqa: D401 - data migration
    Menu = apps.get_model("system", "Menu")
    MenuMeta = apps.get_model("system", "MenuMeta")
    paths = [
        "/hr",
        "/hr/departments",
        "/hr/employees",
        "/hr/attendance/rules",
        "/hr/attendance/summary",
        "/hr/payroll/rules",
        "/hr/payroll/records",
    ]
    metas = list(Menu.objects.filter(path__in=paths).values_list("meta_id", flat=True))
    Menu.objects.filter(path__in=paths).delete()
    MenuMeta.objects.filter(id__in=[pk for pk in metas if pk]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("hr", "0001_initial"),
        ("system", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_hr_menu, remove_hr_menu),
    ]
