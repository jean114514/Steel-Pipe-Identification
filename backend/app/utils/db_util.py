from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库连接信息（请根据你的实际情况修改密码）
# 格式：mysql+pymysql://用户名:密码@地址:端口/数据库名

# 原来的（MySQL）：
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/钢管计数"

# 改成这样（SQLite）：
SQLALCHEMY_DATABASE_URL = "sqlite:///./steel.db"

# 创建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 定期检测连接
    pool_recycle=3600     # 连接超时时间
)

# 创建会话类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()

# 数据库依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()