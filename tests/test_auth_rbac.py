"""
Unit and integration tests for ProjectVision RBAC Authentication & System Control Gating.
Validates:
1. User authentication, password hashing, and session management.
2. Role-based permissions (Admin, Faculty, Student).
3. Role-specific dashboard telemetry synthesis for the React Admin Dashboard.
4. System start/stop gating: cameras start ONLY upon authorized user action.
"""

import unittest
from core.auth import auth_manager, Role
from services.pipeline_manager import pipeline_manager
from api.app import create_app


class TestAuthRBAC(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app(start_pipelines=False)
        cls.client = cls.app.test_client()

    def setUp(self):
        # Ensure system is stopped before each test
        pipeline_manager.stop_all()

    def tearDown(self):
        pipeline_manager.stop_all()

    def test_default_users_seeded(self):
        """Verify pre-configured RBAC users exist with appropriate roles."""
        admin = auth_manager.get_user_by_email("admin@vision.ai")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["role"], Role.ADMIN)

        faculty = auth_manager.get_user_by_email("faculty@vision.ai")
        self.assertIsNotNone(faculty)
        self.assertEqual(faculty["role"], Role.FACULTY)

        student = auth_manager.get_user_by_email("student@vision.ai")
        self.assertIsNotNone(student)
        self.assertEqual(student["role"], Role.STUDENT)

    def test_authentication_logic(self):
        """Verify authentication success and failure handling."""
        # Success
        user = auth_manager.authenticate("admin@vision.ai", "Admin@123")
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "System Administrator")
        self.assertNotIn("password_hash", user)

        # Wrong password
        bad_pass = auth_manager.authenticate("admin@vision.ai", "WrongPassword")
        self.assertIsNone(bad_pass)

        # Non-existent user
        no_user = auth_manager.authenticate("ghost@vision.ai", "Admin@123")
        self.assertIsNone(no_user)

    def test_login_logout_flow(self):
        """Verify /api/auth/login, /api/auth/me, and /api/auth/logout."""
        # 1. Initially unauthenticated
        resp_me = self.client.get('/api/auth/me')
        self.assertEqual(resp_me.status_code, 200)
        self.assertFalse(resp_me.get_json()["authenticated"])

        # 2. Login as Faculty
        resp_login = self.client.post('/api/auth/login', json={
            "email": "faculty@vision.ai",
            "password": "Faculty@123"
        })
        self.assertEqual(resp_login.status_code, 200)
        login_data = resp_login.get_json()
        self.assertTrue(login_data["success"])
        self.assertEqual(login_data["user"]["role"], Role.FACULTY)

        # 3. Check /api/auth/me reflects active session
        resp_me2 = self.client.get('/api/auth/me')
        self.assertEqual(resp_me2.status_code, 200)
        me_data = resp_me2.get_json()
        self.assertTrue(me_data["authenticated"])
        self.assertEqual(me_data["user"]["email"], "faculty@vision.ai")

        # 4. Logout
        resp_logout = self.client.post('/api/auth/logout')
        self.assertEqual(resp_logout.status_code, 200)

        # 5. Verify unauthenticated again
        resp_me3 = self.client.get('/api/auth/me')
        self.assertFalse(resp_me3.get_json()["authenticated"])

    def test_user_specific_dashboard_synthesis(self):
        """Verify dashboard data is customized per role (Admin, Faculty, Student)."""
        admin_user = auth_manager.get_user_by_email("admin@vision.ai")
        faculty_user = auth_manager.get_user_by_email("faculty@vision.ai")
        student_user = auth_manager.get_user_by_email("student@vision.ai")

        admin_data = auth_manager.get_user_specific_dashboard_data(admin_user)
        faculty_data = auth_manager.get_user_specific_dashboard_data(faculty_user)
        student_data = auth_manager.get_user_specific_dashboard_data(student_user)

        # Admin checks
        self.assertEqual(admin_data["role"], Role.ADMIN)
        self.assertTrue(admin_data["system_controls_enabled"])
        self.assertIn("Command", admin_data["title"])

        # Faculty checks
        self.assertEqual(faculty_data["role"], Role.FACULTY)
        self.assertTrue(faculty_data["system_controls_enabled"])
        self.assertIn("Faculty Class Analytics", faculty_data["title"])

        # Student checks
        self.assertEqual(student_data["role"], Role.STUDENT)
        self.assertFalse(student_data["system_controls_enabled"])
        self.assertIn("Personal Learning Portal", student_data["title"])

    def test_system_gating_start_and_stop(self):
        """
        Verify cameras are NOT running on startup and start ONLY when triggered.
        Verify role-based execution gating.
        """
        # 1. System starts in STANDBY
        resp_status = self.client.get('/api/system/status')
        self.assertEqual(resp_status.status_code, 200)
        self.assertFalse(resp_status.get_json()["active"])
        self.assertEqual(resp_status.get_json()["status"], "STANDBY")

        # 2. Student role CANNOT start system (403 Forbidden)
        self.client.post('/api/auth/login', json={"email": "student@vision.ai", "password": "Student@123"})
        resp_start_student = self.client.post('/api/system/start')
        self.assertEqual(resp_start_student.status_code, 403)
        self.assertFalse(pipeline_manager.is_active)

        # 3. Admin role CAN start system (200 OK)
        self.client.post('/api/auth/login', json={"email": "admin@vision.ai", "password": "Admin@123"})
        resp_start_admin = self.client.post('/api/system/start')
        self.assertEqual(resp_start_admin.status_code, 200)
        self.assertTrue(resp_start_admin.get_json()["active"])
        self.assertTrue(pipeline_manager.is_active)

        # 4. Stop system via API
        resp_stop = self.client.post('/api/system/stop')
        self.assertEqual(resp_stop.status_code, 200)
        self.assertFalse(resp_stop.get_json()["active"])
        self.assertFalse(pipeline_manager.is_active)


if __name__ == '__main__':
    unittest.main()

