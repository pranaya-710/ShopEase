import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change_this_later")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "host.docker.internal")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = os.getenv("MYSQL_DB", "shopease")