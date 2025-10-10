"""
API认证中间件和依赖
"""
from fastapi import Header, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Optional
from app.db.database import get_db
from app.db.models import APIKey, APIRequestLog

class AuthenticationError(HTTPException):
    """认证错误异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)


class RateLimitError(HTTPException):
    """频率限制错误异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=429, detail=detail)


async def verify_api_key(
    x_api_key: str = Header(..., description="API密钥"),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    验证API密钥的依赖函数
    
    Args:
        x_api_key: 从请求头中获取的API密钥
        db: 数据库会话
        
    Returns:
        APIKey: 验证通过的API密钥对象
        
    Raises:
        AuthenticationError: 认证失败
        RateLimitError: 超过频率限制
    """
    # 查询API密钥
    api_key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
    
    if not api_key:
        raise AuthenticationError("无效的API密钥")
    
    if not api_key.is_active:
        raise AuthenticationError("API密钥已被禁用")
    
    # 检查是否过期
    if api_key.expires_at and api_key.expires_at < datetime.now():
        raise AuthenticationError("API密钥已过期")
    
    # 检查频率限制
    await check_rate_limit(api_key, db)
    
    return api_key


async def check_rate_limit(api_key: APIKey, db: Session):
    """
    检查API密钥的频率限制
    
    Args:
        api_key: API密钥对象
        db: 数据库会话
        
    Raises:
        RateLimitError: 超过频率限制
    """
    now = datetime.now()
    
    # 检查每分钟限制
    if api_key.rate_limit_per_minute:
        minute_ago = now - timedelta(minutes=1)
        minute_count = db.query(func.count(APIRequestLog.id)).filter(
            and_(
                APIRequestLog.api_key == api_key.key,
                APIRequestLog.created_at >= minute_ago
            )
        ).scalar()
        
        if minute_count >= api_key.rate_limit_per_minute:
            raise RateLimitError(f"超过每分钟请求限制（{api_key.rate_limit_per_minute}次）")
    
    # 检查每小时限制
    if api_key.rate_limit_per_hour:
        hour_ago = now - timedelta(hours=1)
        hour_count = db.query(func.count(APIRequestLog.id)).filter(
            and_(
                APIRequestLog.api_key == api_key.key,
                APIRequestLog.created_at >= hour_ago
            )
        ).scalar()
        
        if hour_count >= api_key.rate_limit_per_hour:
            raise RateLimitError(f"超过每小时请求限制（{api_key.rate_limit_per_hour}次）")
    
    # 检查每天限制
    if api_key.rate_limit_per_day:
        day_ago = now - timedelta(days=1)
        day_count = db.query(func.count(APIRequestLog.id)).filter(
            and_(
                APIRequestLog.api_key == api_key.key,
                APIRequestLog.created_at >= day_ago
            )
        ).scalar()
        
        if day_count >= api_key.rate_limit_per_day:
            raise RateLimitError(f"超过每天请求限制（{api_key.rate_limit_per_day}次）")


async def log_api_request(
    request: Request,
    api_key: APIKey,
    db: Session,
    url: Optional[str] = None,
    status_code: int = 200,
    success: bool = True,
    error_message: Optional[str] = None,
    processing_time: Optional[int] = None,
    response_size: Optional[int] = None
):
    """
    记录API请求日志
    
    Args:
        request: FastAPI请求对象
        api_key: API密钥对象
        db: 数据库会话
        url: 请求的文章URL
        status_code: HTTP状态码
        success: 是否成功
        error_message: 错误信息
        processing_time: 处理时间（毫秒）
        response_size: 响应大小（字节）
    """
    # 获取客户端IP
    client_ip = request.client.host if request.client else None
    
    # 获取User-Agent
    user_agent = request.headers.get("user-agent", "")
    
    # 创建日志记录
    log = APIRequestLog(
        api_key=api_key.key,
        user_id=api_key.user_id,
        endpoint=str(request.url.path),
        method=request.method,
        url=url,
        status_code=status_code,
        success=success,
        error_message=error_message,
        processing_time=processing_time,
        response_size=response_size,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    db.add(log)
    
    # 更新API密钥的统计信息
    api_key.total_requests += 1
    api_key.last_used_at = datetime.now()
    
    db.commit()
