from locust import HttpUser, task, between

MOBILE_UA = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36"

LOGIN_PATH = "/api/v1/auth/login"
PHONE = "01712345678"
PASSWORD = "Test@1234"


class MobileUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.client.headers.update({"User-Agent": MOBILE_UA})

    @task(5)
    def health(self):
        self.client.get("/health")

    @task(1)
    def login(self):
        self.client.post(
            LOGIN_PATH,
            json={"phone_number": PHONE, "password": PASSWORD},
        )