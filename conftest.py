import time
import pytest
from core.config import config
from core.db import SessionLocal, init_db
from models.test_result import TestResult


@pytest.fixture(scope="session", autouse=True)
def verify_env():
    # 测试启动时校验必要环境变量已加载，避免因缺少 Key 导致所有用例静默失败
    assert config.amap_api_key, "AMAP_API_KEY not loaded — check .env file"


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # 测试开始前确保数据库表已创建
    init_db()


@pytest.fixture(autouse=True)
def record_result(request, setup_db):
    # 每条用例执行完后将结果写入 SQLite，供 FastAPI /results 查询
    start = time.time()
    outcome = {"status": "passed", "error_message": None}

    yield

    duration = round(time.time() - start, 3)

    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        outcome["status"] = "failed"
        outcome["error_message"] = str(request.node.rep_call.longrepr)

    db = SessionLocal()
    try:
        db.add(TestResult(
            test_name=request.node.nodeid,
            status=outcome["status"],
            duration=duration,
            error_message=outcome["error_message"],
        ))
        db.commit()
    finally:
        db.close()

    time.sleep(0.3)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # pytest hook：把用例执行报告挂到 item 上，让 record_result fixture 能读取
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
