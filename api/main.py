from fastapi import FastAPI

app = FastAPI(title="Smart API Test Platform")


@app.get("/health")
def health():
    # 服务存活检查，部署后用此端点确认容器启动成功
    return {"status": "ok"}


@app.get("/results")
def list_results():
    # 返回测试执行历史，Week 4 接入 SQLite 后替换为真实数据
    return {"total": 0, "results": []}
