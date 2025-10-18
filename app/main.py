from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import article, file
from app.core.config import settings
from app.services.file_service import FileDownloadThreadPool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
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
    description="下载CSDN文章和文档（无认证版本）",
    version="3.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(article.router, prefix="/api/article", tags=["文章"])
app.include_router(file.router, prefix="/api/file", tags=["文件下载"])

@app.get("/")
async def root():
    return {
        "message": "CSDN文章下载器API",
        "version": "3.0.0",
        "features": ["Celery异步队列", "无需认证", "简化架构"]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)