from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from django.db import transaction

from apps.dingtalk.models import DingTalkDepartment, DingTalkUser

from ..models import Department, Employee


@dataclass(slots=True)
class ImportResult:
    created: int = 0
    updated: int = 0


class DepartmentImporter:
    """将钉钉部门映射到本地人力资源模块"""

    def __init__(self, *, config_id: str | None = None) -> None:
        self.config_id = config_id

    def fetch(self) -> Sequence[DingTalkDepartment]:
        queryset = DingTalkDepartment.objects.all()
        if self.config_id:
            queryset = queryset.filter(config_id=self.config_id)
        return list(queryset.order_by("dept_id"))

    @transaction.atomic
    def sync(self, departments: Iterable[DingTalkDepartment] | None = None) -> ImportResult:
        result = ImportResult()
        items = list(departments) if departments is not None else self.fetch()
        indexed: dict[int, Department] = {
            int(item.ding_department.dept_id): item
            for item in Department.objects.filter(ding_department__isnull=False)
        }
        for dept in items:
            source_info = dept.source_info if isinstance(dept.source_info, dict) else {}
            description = ""
            if source_info:
                description = str(source_info.get("brief", source_info.get("name", "")))
            defaults = {
                "name": dept.name,
                "code": str(dept.dept_id),
                "config_id": str(self.config_id or dept.config_id or ""),
                "description": description,
                "metadata": source_info,
            }
            parent = None
            if dept.parent_id:
                parent = indexed.get(dept.parent_id) or Department.objects.filter(
                    ding_department__dept_id=dept.parent_id
                ).first()
            defaults["parent"] = parent
            instance, created = Department.objects.update_or_create(
                ding_department=dept,
                defaults=defaults,
            )
            indexed[int(dept.dept_id)] = instance
            if created:
                result.created += 1
            else:
                result.updated += 1
        return result


class EmployeeImporter:
    """将钉钉员工映射到人力资源模块"""

    def __init__(self, *, config_id: str | None = None) -> None:
        self.config_id = config_id

    def fetch(self) -> Sequence[DingTalkUser]:
        queryset = DingTalkUser.objects.all()
        if self.config_id:
            queryset = queryset.filter(config_id=self.config_id)
        return list(queryset.order_by("userid"))

    @transaction.atomic
    def sync(self, users: Iterable[DingTalkUser] | None = None) -> ImportResult:
        result = ImportResult()
        items = list(users) if users is not None else self.fetch()
        dept_map = {
            str(dept.ding_department.dept_id): dept
            for dept in Department.objects.filter(ding_department__isnull=False)
        }
        for user in items:
            dept_id = str(user.dept_ids[0]) if user.dept_ids else None
            department = dept_map.get(dept_id)
            source_info = user.source_info if isinstance(user.source_info, dict) else {}
            defaults = {
                "name": user.name or user.userid,
                "job_number": user.job_number or user.userid,
                "config_id": str(self.config_id or getattr(user, "config_id", "") or ""),
                "email": user.email or "",
                "phone": user.mobile or "",
                "title": user.title or "",
                "metadata": source_info,
            }
            if department is not None:
                defaults["department"] = department
            instance, created = Employee.objects.update_or_create(
                ding_user=user,
                defaults=defaults,
            )
            if created:
                result.created += 1
            else:
                result.updated += 1
        return result
