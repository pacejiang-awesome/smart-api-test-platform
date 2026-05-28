import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 允许通过环境变量覆盖，便于不同部署环境使用不同数据库路径
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test_results.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


def init_db():
    # 根据所有模型类在数据库创建对应表，已存在则跳过
    Base.metadata.create_all(bind=engine)
