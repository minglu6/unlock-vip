from fastapi import FastAPI
from app.api import article, file
from app.core.config import settings

app = FastAPI(
    title="CSDN文章下载器",
    description="下载CSDN文章和文档（同步版）",
    version="5.0.0"
)

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