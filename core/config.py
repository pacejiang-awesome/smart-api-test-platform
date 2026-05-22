import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    AMAP_BASE_URL = "https://restapi.amap.com/v3"
    TIMEOUT = 5

    def __init__(self):
        self.amap_api_key = self._require("AMAP_API_KEY")

    @staticmethod
    def _require(key: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise EnvironmentError(f"Missing required environment variable: {key}")
        return value


config = Config()
