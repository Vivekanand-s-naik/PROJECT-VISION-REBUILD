"""
Unit and integration tests for ProjectVision REST API & Dashboard Endpoints (Phases 7 & 8).
Validates Flask application routes, data endpoints, health checks, and HTML view rendering.
"""

import unittest
from api.app import create_app


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create Flask app with test client (without starting continuous background camera threads for quick testing)
        cls.app = create_app(start_pipelines=False)
        cls.client = cls.app.test_client()

    def test_health_endpoint(self):
        """Verify /api/health returns status, pipelines, and blockchain status."""
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("status", data)
        self.assertIn("pipelines", data)
        self.assertIn("blockchain", data)
        self.assertTrue(data["blockchain"]["valid"])

    def test_user_data_endpoints(self):
        """Verify /get_user_data and /api/user_data format."""
        resp = self.client.get('/get_user_data')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("detected", data)

        resp2 = self.client.get('/api/user_data')
        self.assertEqual(resp2.status_code, 200)

    def test_students_endpoint(self):
        """Verify /api/students list."""
        resp = self.client.get('/api/students')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(data["count"], 0)

    def test_attendance_summary(self):
        """Verify /api/attendance/summary counter aggregation."""
        resp = self.client.get('/api/attendance/summary')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("total_registered_students", data["summary"])

    def test_stats_and_reset(self):
        """Verify /api/stats and /api/reset_stats."""
        resp = self.client.get('/api/stats')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("total_faces_detected", data)

        resp_reset = self.client.post('/api/reset_stats')
        self.assertEqual(resp_reset.status_code, 200)

    def test_blockchain_endpoints(self):
        """Verify /api/blockchain and /api/blockchain/verify."""
        resp = self.client.get('/api/blockchain')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["chain_valid"])

        resp_verify = self.client.get('/api/blockchain/verify')
        self.assertEqual(resp_verify.status_code, 200)
        self.assertTrue(resp_verify.get_json()["is_valid"])

    def test_speech_summarize_endpoint(self):
        """Verify /api/speech/summarize NLP endpoint."""
        text = "Deep learning and artificial intelligence improve classroom attendance and safety."
        resp = self.client.post('/api/speech/summarize', json={"text": text})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("summary", data)

    def test_html_dashboard_views(self):
        """Verify all HTML template views and GP root render with HTTP 200."""
        routes = ['/', '/dashboard', '/grid', '/notes', '/blockchain', '/students', '/react']
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed with {resp.status_code}")

    def test_gp_and_react_endpoints(self):
        """Verify GP landing page interactive triggers and React app routes."""
        resp_act = self.client.post('/activate')
        self.assertEqual(resp_act.status_code, 200)
        self.assertTrue(resp_act.get_json()["success"])

        resp_noter = self.client.post('/run_noter_script')
        self.assertEqual(resp_noter.status_code, 200)
        self.assertTrue(resp_noter.get_json()["success"])

        resp_react = self.client.get('/react/')
        self.assertEqual(resp_react.status_code, 200)
        self.assertIn(b"root", resp_react.data)


if __name__ == "__main__":
    unittest.main()

