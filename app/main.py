from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import article, admin, file
from app.core.config import settings
from app.db.database import init_db
from app.services.file_service import FileDownloadThreadPool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    print("正在初始化数据库...")
    init_db()
    print("数据库初始化完成")
    
    # 初始化文件下载服务线程池
    print("正在初始化文件下载服务线程池...")
    FileDownloadThreadPool()
    print("文件下载服务线程池初始化完成（4个工作线程）")
    
    yield
    
    # 关闭时的清理工作
    print("应用正在关闭...")
    print("正在关闭文件下载服务线程池...")
    FileDownloadThreadPool().shutdown(wait=True)
    print("文件下载服务线程池已关闭")

app = FastAPI(
    title="CSDN文章下载器",
    description="模拟登录CSDN并下载文章HTML（带API认证）",
    version="2.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(article.router, prefix="/api/article", tags=["文章"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(file.router, prefix="/api/file", tags=["文件下载"])

@app.get("/")
async def root():
    return {
        "message": "CSDN文章下载器API",
        "version": "2.0.0",
        "features": ["Celery异步队列", "API Key认证", "请求日志记录", "频率限制"]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)