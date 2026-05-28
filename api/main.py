from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from core.db import SessionLocal, init_db
from models.test_result import TestResult

app = FastAPI(title="Smart API Test Platform")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
init_db()


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("web/templates/index.html")


def get_db():
    # FastAPI 依赖注入：每个请求得到一个独立 session，请求结束自动关闭
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    # 服务存活检查，部署后用此端点确认容器启动成功
    return {"status": "ok"}


@app.get("/results")
def list_results(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    # 先查总数再分页，确保 total 反映全量记录数而非当前页条数
    total = db.query(TestResult).count()
    rows = (
        db.query(TestResult)
        .order_by(TestResult.run_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [
            {
                "id": r.id,
                "test_name": r.test_name,
                "status": r.status,
                "duration": r.duration,
                "run_at": r.run_at.isoformat(),
                "error_message": r.error_message,
            }
            for r in rows
        ],
    }
