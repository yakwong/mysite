from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


User = get_user_model()


@override_settings(DEBUG=True, API_LOG_ENABLE=False)
class LoginAPITests(TestCase):
    """登录接口相关测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="loginuser@example.com",
            username="loginuser",
            password="LoginUser123!",
        )

    def test_login_allows_account_with_whitespace(self):
        response = self.client.post(
            "/api/user/login/",
            {"account": "  loginuser@example.com  ", "password": "LoginUser123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, msg=response.content.decode())
        payload = response.json()
        self.assertTrue(payload.get("success"))
        data = payload.get("data", {})
        self.assertEqual(data.get("username"), "loginuser")
        self.assertIn("accessToken", data)


@override_settings(DEBUG=True, API_LOG_ENABLE=False)
class AccountSecurityAPITests(TestCase):
    """账户设置安全相关接口测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="tester@example.com",
            username="tester",
            password="OldPass123!",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _extract_code(self, response):
        self.assertEqual(response.status_code, 200, msg=response.content.decode())
        payload = response.json()
        self.assertTrue(payload.get("success"))
        data = payload.get("data", {})
        code = data.get("code")
        self.assertIsNotNone(code, "测试环境应返回验证码")
        return code

    def test_change_password_updates_strength_and_timestamp(self):
        response = self.client.post(
            "/api/user/profile/change-password/",
            {
                "old_password": "OldPass123!",
                "new_password": "NewPass123!@#",
                "confirm_password": "NewPass123!@#",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass123!@#"))
        self.assertEqual(self.user.password_strength, "strong")
        self.assertIsNotNone(self.user.password_updated_at)

    def test_bind_and_unbind_phone_requires_verification_code(self):
        bind_code = self._extract_code(
            self.client.post(
                "/api/user/profile/send-code/",
                {"action": "bind_phone", "target": "13800138000"},
                format="json",
            )
        )
        bind_response = self.client.post(
            "/api/user/profile/bind-phone/",
            {"phone": "13800138000", "code": bind_code},
            format="json",
        )
        self.assertEqual(bind_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "13800138000")
        self.assertTrue(self.user.phone_verified)

        unbind_code = self._extract_code(
            self.client.post(
                "/api/user/profile/send-code/",
                {"action": "unbind_phone"},
                format="json",
            )
        )
        unbind_response = self.client.post(
            "/api/user/profile/unbind-phone/",
            {"code": unbind_code},
            format="json",
        )
        self.assertEqual(unbind_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone)
        self.assertFalse(self.user.phone_verified)

    def test_backup_email_bind_and_remove(self):
        code = self._extract_code(
            self.client.post(
                "/api/user/profile/send-code/",
                {"action": "backup_email", "target": "backup@example.com"},
                format="json",
            )
        )
        bind_response = self.client.post(
            "/api/user/profile/backup-email/",
            {"backup_email": "backup@example.com", "code": code},
            format="json",
        )
        self.assertEqual(bind_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.backup_email, "backup@example.com")

        remove_response = self.client.delete("/api/user/profile/backup-email/")
        self.assertEqual(remove_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.backup_email)

    def test_security_question_set_update_and_clear(self):
        set_response = self.client.post(
            "/api/user/profile/security-question/",
            {"question": "测试问题?", "answer": "答案123"},
            format="json",
        )
        self.assertEqual(set_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.security_question, "测试问题?")
        self.assertTrue(self.user.security_answer_hash)

        update_response = self.client.post(
            "/api/user/profile/security-question/",
            {
                "question": "新的问题?",
                "answer": "新答案456",
                "current_answer": "答案123",
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.security_question, "新的问题?")

        clear_response = self.client.delete("/api/user/profile/security-question/")
        self.assertEqual(clear_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.security_question)
        self.assertIsNone(self.user.security_answer_hash)

    def test_toggle_login_notifier(self):
        self.assertTrue(self.user.login_notifier_enabled)

        disable_response = self.client.post(
            "/api/user/profile/login-notifier/",
            {"enabled": False},
            format="json",
        )
        self.assertEqual(disable_response.status_code, 200)
        payload = disable_response.json()
        self.assertTrue(payload.get("success"))
        self.assertFalse(payload["data"]["login_notifier_enabled"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.login_notifier_enabled)

        enable_response = self.client.post(
            "/api/user/profile/login-notifier/",
            {"enabled": True},
            format="json",
        )
        self.assertEqual(enable_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.login_notifier_enabled)

    def test_security_state_overview_contains_masked_values(self):
        self.user.phone = "13800138000"
        self.user.phone_verified = True
        self.user.backup_email = "backup@example.com"
        self.user.two_factor_enabled = True
        self.user.save(
            update_fields=[
                "phone",
                "phone_verified",
                "backup_email",
                "two_factor_enabled",
            ]
        )

        response = self.client.get("/api/user/profile/security-state/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        data = payload["data"]
        self.assertEqual(data["masked_phone"], "138****8000")
        self.assertEqual(data["masked_backup_email"], "b***p@example.com")
        self.assertTrue(data["two_factor_enabled"])
