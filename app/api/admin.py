"""
管理接口 - API密钥管理和统计
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, Integer
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import secrets

from app.db.database import get_db
from app.db.models import APIKey, APIRequestLog
from app.core.config import settings

router = APIRouter()


# ===== 管理员认证依赖 =====

async def verify_admin_key(x_admin_key: str = Header(..., description="管理员主密钥")):
    """
    验证管理员主密钥
    
    Args:
        x_admin_key: HTTP头中的管理员密钥
    
    Raises:
        HTTPException: 如果密钥无效或未配置
    """
    if not settings.ADMIN_MASTER_KEY:
        raise HTTPException(
            status_code=500,
            detail="服务器未配置管理员密钥，请联系系统管理员"
        )
    
    if x_admin_key != settings.ADMIN_MASTER_KEY:
        raise HTTPException(
            status_code=403,
            detail="无效的管理员密钥"
        )
    
    return True


# ===== Pydantic 模型 =====

class APIKeyCreate(BaseModel):
    """创建API密钥请求"""
    name: str
    user_id: Optional[str] = None
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    expires_days: Optional[int] = None  # 过期天数，None表示永不过期
    description: Optional[str] = None


class APIKeyResponse(BaseModel):
    """API密钥响应"""
    id: int
    key: str
    name: str
    user_id: Optional[str]
    is_active: bool
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    rate_limit_per_day: int
    total_requests: int
    last_used_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]
    description: Optional[str]

    class Config:
        from_attributes = True


class APIKeyStats(BaseModel):
    """API密钥统计"""
    api_key: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_processing_time: Optional[float]
    last_request_at: Optional[datetime]


class RequestLogResponse(BaseModel):
    """请求日志响应"""
    id: int
    api_key: str
    endpoint: str
    method: str
    url: Optional[str]
    status_code: Optional[int]
    success: bool
    error_message: Optional[str]
    processing_time: Optional[int]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 管理接口 =====

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    创建新的API密钥
    
    需要管理员权限（X-Admin-Key header）
    """
    # 生成32字节的随机密钥
    api_key = secrets.token_urlsafe(32)
    
    # 计算过期时间
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.now() + timedelta(days=key_data.expires_days)
    
    # 创建数据库记录
    db_api_key = APIKey(
        key=api_key,
        name=key_data.name,
        user_id=key_data.user_id,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        rate_limit_per_day=key_data.rate_limit_per_day,
        expires_at=expires_at,
        description=key_data.description
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return db_api_key


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    列出所有API密钥
    
    需要管理员权限（X-Admin-Key header）
    """
    query = db.query(APIKey)
    
    if user_id:
        query = query.filter(APIKey.user_id == user_id)
    
    if is_active is not None:
        query = query.filter(APIKey.is_active == is_active)
    
    api_keys = query.offset(skip).limit(limit).all()
    return api_keys


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    获取指定API密钥详情
    
    需要管理员权限（X-Admin-Key header）
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API密钥不存在")
    return api_key


@router.put("/api-keys/{key_id}/toggle")
async def toggle_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    启用/禁用API密钥
    
    需要管理员权限（X-Admin-Key header）
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API密钥不存在")
    
    api_key.is_active = not api_key.is_active
    db.commit()
    
    return {"message": f"API密钥已{'启用' if api_key.is_active else '禁用'}", "is_active": api_key.is_active}


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    删除API密钥
    
    需要管理员权限（X-Admin-Key header）
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API密钥不存在")
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API密钥已删除"}


@router.get("/api-keys/{key_id}/stats", response_model=APIKeyStats)
async def get_api_key_stats(
    key_id: int,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    获取API密钥的统计信息
    
    需要管理员权限（X-Admin-Key header）
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API密钥不存在")
    
    # 计算时间范围
    start_date = datetime.now() - timedelta(days=days)
    
    # 统计查询
    stats = db.query(
        func.count(APIRequestLog.id).label('total'),
        func.sum(func.cast(APIRequestLog.success, Integer)).label('successful'),
        func.avg(APIRequestLog.processing_time).label('avg_time'),
        func.max(APIRequestLog.created_at).label('last_request')
    ).filter(
        and_(
            APIRequestLog.api_key == api_key.key,
            APIRequestLog.created_at >= start_date
        )
    ).first()
    
    total = stats.total or 0
    successful = stats.successful or 0
    
    return APIKeyStats(
        api_key=api_key.key,
        total_requests=total,
        successful_requests=successful,
        failed_requests=total - successful,
        avg_processing_time=stats.avg_time,
        last_request_at=stats.last_request
    )


@router.get("/logs", response_model=List[RequestLogResponse])
async def get_request_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    api_key: Optional[str] = None,
    user_id: Optional[str] = None,
    success: Optional[bool] = None,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    获取API请求日志
    
    需要管理员权限（X-Admin-Key header）
    """
    start_date = datetime.now() - timedelta(days=days)
    
    query = db.query(APIRequestLog).filter(APIRequestLog.created_at >= start_date)
    
    if api_key:
        query = query.filter(APIRequestLog.api_key == api_key)
    
    if user_id:
        query = query.filter(APIRequestLog.user_id == user_id)
    
    if success is not None:
        query = query.filter(APIRequestLog.success == success)
    
    logs = query.order_by(APIRequestLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs


# ===== 文件清理管理接口 =====

@router.get("/cleanup/stats")
async def get_cleanup_stats(
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    获取下载目录的统计信息
    
    需要管理员权限（X-Admin-Key header）
    """
    from app.tasks.cleanup_tasks import get_downloads_stats
    
    # 直接执行任务（同步）
    stats = get_downloads_stats()
    return stats


@router.post("/cleanup/run")
async def run_cleanup(
    days: int = Query(7, ge=1, le=365, description="保留天数"),
    dry_run: bool = Query(False, description="演练模式（不实际删除）"),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    手动触发文件清理任务
    
    需要管理员权限（X-Admin-Key header）
    
    Args:
        days: 保留天数，默认7天
        dry_run: 是否为演练模式（不实际删除），默认False
    """
    from app.tasks.cleanup_tasks import cleanup_old_downloads
    
    # 可以选择同步或异步执行
    # 同步执行（立即返回结果）
    result = cleanup_old_downloads(days=days, dry_run=dry_run)
    
    # 异步执行（返回任务ID）
    # task = cleanup_old_downloads.delay(days=days, dry_run=dry_run)
    # return {"task_id": task.id, "status": "submitted"}
    
    return result


@router.get("/cleanup/config")
async def get_cleanup_config(
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    获取清理任务配置
    
    需要管理员权限（X-Admin-Key header）
    """
    from app.core.config import settings
    
    return {
        "enabled": settings.CLEANUP_ENABLED,
        "retention_days": settings.CLEANUP_RETENTION_DAYS,
        "schedule": "每24小时执行一次",
        "timezone": "Asia/Shanghai"
    }


@router.put("/cleanup/config")
async def update_cleanup_config(
    retention_days: int = Query(..., ge=1, le=365),
    admin_verified: bool = Depends(verify_admin_key)
):
    """
    更新清理任务配置（需要重启服务生效）
    
    需要管理员权限（X-Admin-Key header）
    
    注意：此接口只返回建议的环境变量配置，需要手动更新.env文件并重启服务
    """
    return {
        "message": "请更新 .env 文件并重启服务",
        "env_config": f"CLEANUP_RETENTION_DAYS={retention_days}",
        "current_value": retention_days
    }
