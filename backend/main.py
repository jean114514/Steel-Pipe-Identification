from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import recognize_router, result_router, manual_router, user_router, inventory_router
from app.utils.db_util import engine, get_db
from app.models.entity import Base
from app.api.user import init_admin_user
import os

# 创建静态文件夹
if not os.path.exists("static"):
    os.makedirs("static")

# 初始化数据库表
try:
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功！")

    # 初始化管理员账号
    db = next(get_db())
    init_admin_user(db)
    db.close()
except Exception as e:
    print(f"❌ 数据库表创建失败: {e}")

# 创建 FastAPI 实例
app = FastAPI(title="钢管计数系统API", version="1.0.0")

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(recognize_router, prefix="/api")
app.include_router(result_router, prefix="/api")
app.include_router(manual_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")  # 新增


# 根路由
@app.get("/")
def root():
    return {"msg": "钢管计数系统后端运行成功！", "status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)