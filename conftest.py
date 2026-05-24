import pytest
from core.config import config


@pytest.fixture(scope="session", autouse=True)
def verify_env():
    # 测试启动时校验必要环境变量已加载，避免因缺少 Key 导致所有用例静默失败
    assert config.amap_api_key, "AMAP_API_KEY not loaded — check .env file"
