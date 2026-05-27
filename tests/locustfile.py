from locust import HttpUser, task, between
import random

class SmartConfUser(HttpUser):
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)

    @task(3)
    def view_dashboard(self):
        """Simulate user viewing the dashboard (list meetings)"""
        self.client.get("/api/meetings")

    @task(2)
    def view_meeting_details(self):
        """Simulate user viewing specific meeting details"""
        # First, get the list of meetings
        with self.client.get("/api/meetings", catch_response=True) as response:
            if response.status_code == 200:
                meetings = response.json()
                if meetings:
                    # Pick a random meeting ID that actually exists
                    meeting_id = random.choice(meetings)["id"]
                    self.client.get(f"/api/meetings/{meeting_id}", name="/api/meetings/[id]")

    @task(5)
    def search_query(self):
        """Simulate natural language search"""
        query = "List the problems of MiniPC model sales"
        self.client.get(f"/api/search?query={query}", name="/api/search")

# To run this script:
# locust -f locustfile.py --host=http://localhost:8000
# In the Locust UI, set concurrent users to 30 and spawn rate to 5
