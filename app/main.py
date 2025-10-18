from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import article, file
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CSDN文章下载器",
    description="下载CSDN文章和文档（同步版）",
    version="5.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求信息
    logger.info(f"收到请求: {request.method} {request.url.path}")
    logger.info(f"请求头: {dict(request.headers)}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"请求处理完成: {request.method} {request.url.path} - 状态码: {response.status_code} - 耗时: {process_time:.2f}s")

    return response

# 注册路由
app.include_router(article.router, prefix="/api/article", tags=["文章"])
app.include_router(file.router, prefix="/api/file", tags=["文件下载"])

@app.get("/")
async def root():
    return {
        "message": "CSDN文章下载器API",
        "version": "5.0.0",
        "features": ["同步下载", "无需认证", "精简架构", "直接返回HTML"]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)