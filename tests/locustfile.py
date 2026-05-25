from locust import HttpUser, task, between

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
        # Assuming meeting ID 1 exists for the test
        self.client.get("/api/meetings/1", name="/api/meetings/[id]")

    @task(5)
    def search_query(self):
        """Simulate natural language search"""
        query = "List the problems of MiniPC model sales"
        self.client.get(f"/api/search?query={query}", name="/api/search")

# To run this script:
# locust -f locustfile.py --host=http://localhost:8000
# In the Locust UI, set concurrent users to 30 and spawn rate to 5
