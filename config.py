import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"
    USERS_DB = "users.db"
    BOOKINGS_DB = "bookings.db"

config = Config()
