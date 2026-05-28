import requests
from core.config import config


class AMapClient:

    def __init__(self):
        self.session = requests.Session()
        self.base_url = config.AMAP_BASE_URL

    def get(self, endpoint: str, params: dict = None) -> requests.Response:
        url = self.base_url + endpoint

        merged_params = {**(params or {}), "key": config.amap_api_key}

        return self.session.get(
            url,
            params=merged_params,
            timeout=config.TIMEOUT
        )


client = AMapClient()
