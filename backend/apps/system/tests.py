from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.system.models import Menu, MenuMeta, Role


class SystemApiTestCase(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="tester@example.com",
            username="tester",
            password="StrongPass!123",
        )
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.role = Role.objects.create(name="系统管理员", code="system_admin")
        self.user.role.add(self.role)
        self.client.force_authenticate(self.user)

    def _create_menu_with_permission(self):
        menu_meta = MenuMeta.objects.create(title="系统管理", icon="ri:mac-line", rank=1, is_show_menu=True)
        menu = Menu.objects.create(
            meta=menu_meta,
            menu_type=Menu.MenuChoices.MENU,
            name="system-menu",
            path="/system",
            component="layout",
            status=True,
        )
        perm_meta = MenuMeta.objects.create(title="菜单查询", rank=10, is_show_menu=False)
        permission = Menu.objects.create(
            parent=menu,
            meta=perm_meta,
            menu_type=Menu.MenuChoices.PERMISSION,
            name="system-menu-read",
            code="/api/system/menu/:read",
            path="/api/system/menu/",
            status=True,
        )
        self.role.menu.add(menu, permission)
        return menu, permission

    def test_role_list_returns_wrapped_payload(self):
        url = reverse("role-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIsInstance(payload["data"], list)

    def test_menu_creation_persists_meta_relationship(self):
        url = reverse("menu-list")
        payload = {
            "menu_type": Menu.MenuChoices.MENU,
            "name": "audit",
            "path": "/audit",
            "component": "views/audit/index.vue",
            "status": True,
            "meta": {
                "title": "审计中心",
                "icon": "ri:spy-line",
                "rank": 20,
                "showLink": True,
                "showParent": False,
                "keepAlive": False,
                "hiddenTag": False,
                "fixedTag": False,
            },
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data["success"])
        created_id = data["data"]["id"]
        menu = Menu.objects.get(id=created_id)
        self.assertIsNotNone(menu.meta)
        self.assertEqual(menu.meta.title, "审计中心")

    def test_async_routes_returns_permission_codes(self):
        self._create_menu_with_permission()
        url = reverse("AsyncRoutesView")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])
        routes = payload["data"]
        self.assertEqual(len(routes), 1)
        meta = routes[0]["meta"]
        self.assertIn("auths", meta)
        self.assertIn("/api/system/menu/:read", meta["auths"])
