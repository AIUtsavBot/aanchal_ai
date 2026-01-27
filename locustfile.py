
from locust import HttpUser, task, between
import random

class SantanRakshaUser(HttpUser):
    wait_time = between(1, 5)
    
    # Authenticate once on start
    def on_start(self):
        # Assuming we have a test user or can signup
        # For load testing, usually good to use a pre-existing token or login
        self.token = None
        response = self.client.post("/api/auth/signin", json={
            "email": "doctor@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print("Login failed, proceeding as anonymous (limited access)")
            self.headers = {}

    @task(3)
    def view_dashboard_data(self):
        if self.token:
            self.client.get("/api/dashboard/stats", headers=self.headers)

    @task(1)
    def health_check(self):
        self.client.get("/health")
    
    @task(2)
    def get_vaccination_schedule(self):
        # Test public/protected endpoint
        if self.token:
            self.client.get("/api/santanraksha/vaccination/schedule/standard", headers=self.headers)

    @task(1)
    def check_ai_prediction(self):
        # Stress test the AI endpoint
        if self.token:
            # Random UUID to simulate valid format (will likely 404 but tests auth/routing)
            fake_id = "00000000-0000-0000-0000-000000000000"
            self.client.get(f"/api/ai/insights/{fake_id}", headers=self.headers)
