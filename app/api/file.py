#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSDN资源下载API端点
提供资源文件下载链接获取接口
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.services.file_service import FileDownloadService, get_thread_pool
from app.middleware.auth import verify_api_key
from app.db.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求模型
class DownloadLinkRequest(BaseModel):
    """获取下载链接请求"""
    url: str = Field(..., description="CSDN资源下载页面URL", example="https://download.csdn.net/download/weixin_43385320/91316313")


# 响应模型
class DownloadLinkResponse(BaseModel):
    """下载链接响应"""
    success: bool = Field(..., description="是否成功")
    download_url: Optional[str] = Field(None, description="资源下载链接")
    source_id: Optional[str] = Field(None, description="资源ID")
    error: Optional[str] = Field(None, description="错误消息")
    message: str = Field(..., description="响应消息")


@router.post("/get-download-link", response_model=DownloadLinkResponse, summary="获取资源下载链接")
async def get_download_link(
    request: DownloadLinkRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    获取CSDN资源的实际下载链接
    
    ## 功能说明
    - 解析CSDN资源下载页面URL
    - 向CSDN下载API发送请求
    - 返回实际的文件下载链接
    
    ## 参数
    - **url**: CSDN资源下载页面URL
    
    ## 返回
    - 成功：返回下载链接
    - 失败：返回错误信息
    
    ## 示例
    ```bash
    curl -X POST "http://localhost:8000/api/file/get-download-link" \\
      -H "X-API-Key: YOUR_API_KEY" \\
      -H "Content-Type: application/json" \\
      -d '{"url": "https://download.csdn.net/download/user/12345"}'
    ```
    
    ## 注意
    - 需要有效的CSDN登录cookies（在cookies.json中配置）
    - 某些资源可能需要VIP权限
    - 下载链接具有时效性（通常1小时）
    - 使用线程池处理（4个工作线程，支持并发请求）
    """
    
    def _process_download_request(url: str) -> DownloadLinkResponse:
        """在线程池中处理下载请求"""
        try:
            # 创建下载服务
            service = FileDownloadService()
            
            # 尝试加载cookies
            service.load_cookies_from_file("cookies.json")
            
            # 提取sourceId
            source_id = service.extract_source_id_from_url(url)
            
            if not source_id:
                logger.warning(f"无法从URL提取sourceId: {url}")
                return DownloadLinkResponse(
                    success=False,
                    source_id=None,
                    download_url=None,
                    error="无效的CSDN下载URL格式",
                    message="URL格式错误，请提供正确的CSDN资源下载链接"
                )
            
            # 获取下载链接
            success, download_url, error = service.get_download_link(source_id)
            
            if success:
                logger.info(f"成功获取下载链接，sourceId: {source_id}")
                return DownloadLinkResponse(
                    success=True,
                    source_id=source_id,
                    download_url=download_url,
                    error=None,
                    message="成功获取下载链接"
                )
            else:
                logger.error(f"获取下载链接失败，sourceId: {source_id}, 错误: {error}")
                return DownloadLinkResponse(
                    success=False,
                    source_id=source_id,
                    download_url=None,
                    error=error,
                    message="获取下载链接失败"
                )
        except Exception as e:
            logger.error(f"处理下载请求时发生错误: {str(e)}", exc_info=True)
            return DownloadLinkResponse(
                success=False,
                source_id=None,
                download_url=None,
                error=str(e),
                message="处理请求时发生错误"
            )
    
    try:
        logger.info(f"收到下载链接请求: {request.url}")
        
        # 获取线程池
        thread_pool = get_thread_pool()
        
        # 在事件循环中执行线程池任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            thread_pool,
            _process_download_request,
            request.url
        )
        
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理下载链接请求时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """
    文件下载服务健康检查
    
    返回服务状态和配置信息
    """
    try:
        # 检查cookies文件
        service = FileDownloadService()
        cookies_loaded = service.load_cookies_from_file("cookies.json")
        
        return {
            "status": "healthy",
            "service": "file_download",
            "cookies_available": cookies_loaded,
            "api_endpoint": FileDownloadService.DOWNLOAD_API
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "file_download",
            "error": str(e)
        }
