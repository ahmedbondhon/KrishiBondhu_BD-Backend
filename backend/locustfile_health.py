from locust import HttpUser, task, between


class HealthUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def health(self):
        self.client.get("/health")
