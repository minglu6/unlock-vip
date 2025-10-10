from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.models.schemas import (
    ArticleRequest, TaskStatusResponse,
    TaskSubmissionResponse, TaskResultResponse
)
from app.tasks.article_tasks import download_and_save_article
from celery.result import AsyncResult
from app.core.celery_app import celery_app
from app.middleware.auth import verify_api_key, log_api_request
from app.db.database import get_db
from app.db.models import APIKey
import time
import uuid
import redis
import json
from urllib.parse import urlparse
from app.core.config import settings

router = APIRouter()

ALLOWED_CSDN_DOMAINS = ['blog.csdn.net', 'wenku.csdn.net']
ALLOWED_SCHEMES = {'http', 'https'}

# Redis 连接用于存储任务结果
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

@router.post("/submit", response_model=TaskSubmissionResponse)
async def submit_download_task(
    request_obj: Request,
    request: ArticleRequest,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    提交文章下载任务

    返回一个UUID作为任务唯一标识符，后台使用Celery异步处理
    调用方需要轮询任务状态接口获取处理进度

    需要在请求头中提供 X-API-Key 进行认证
    """
    start_time = time.time()
    url = request.url

    # 验证URL
    parsed_url = urlparse(url)
    hostname = (parsed_url.hostname or '').lower()
    scheme = parsed_url.scheme.lower()
    is_valid_scheme = scheme in ALLOWED_SCHEMES

    # 检查域名是否在允许列表中
    is_valid_host = False
    for allowed_domain in ALLOWED_CSDN_DOMAINS:
        if hostname == allowed_domain or hostname.endswith(f'.{allowed_domain}'):
            is_valid_host = True
            break

    # 根据域名类型检查路径格式
    is_valid_path = False
    if 'blog.csdn.net' in hostname:
        is_valid_path = '/article/details/' in parsed_url.path
    elif 'wenku.csdn.net' in hostname:
        # 仅支持具体的/answer/路径格式（基于提供的具体接口）
        is_valid_path = '/answer/' in parsed_url.path

    if not (is_valid_scheme and hostname and is_valid_host and is_valid_path):
        processing_time_ms = int((time.time() - start_time) * 1000)
        error_detail = '请提供有效的CSDN博客文章或文库文档链接'
        await log_api_request(
            request=request_obj,
            api_key=api_key,
            db=db,
            url=url,
            status_code=400,
            success=False,
            error_message=error_detail,
            processing_time=processing_time_ms
        )
        raise HTTPException(status_code=400, detail=error_detail)

    try:
        # 生成UUID作为任务ID
        task_id = str(uuid.uuid4())

        # 提交异步任务到Celery
        download_and_save_article.apply_async(
            args=[url],
            task_id=task_id  # 使用生成的UUID作为任务ID
        )

        # 记录成功提交日志
        processing_time = int((time.time() - start_time) * 1000)
        await log_api_request(
            request=request_obj,
            api_key=api_key,
            db=db,
            url=url,
            status_code=200,
            success=True,
            processing_time=processing_time
        )

        return TaskSubmissionResponse(
            task_id=task_id,
            status="PENDING",
            message="任务已成功提交，请使用任务ID轮询状态"
        )

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        await log_api_request(
            request=request_obj,
            api_key=api_key,
            db=db,
            url=url,
            status_code=500,
            success=False,
            error_message=str(e),
            processing_time=processing_time
        )

        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")

@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    request_obj: Request,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    查询任务状态

    状态说明：
    - PENDING: 任务等待中
    - PROCESSING: 任务处理中
    - SUCCESS: 任务成功
    - FAILURE: 任务失败
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        # 获取进度信息（如果任务支持）
        progress = None
        if hasattr(task_result, 'info') and task_result.info:
            if isinstance(task_result.info, dict) and 'progress' in task_result.info:
                progress = task_result.info['progress']

        if task_result.state == 'PENDING':
            return TaskStatusResponse(
                task_id=task_id,
                status='PENDING',
                progress=progress,
                result=None,
                error=None
            )
        elif task_result.state == 'PROCESSING':
            return TaskStatusResponse(
                task_id=task_id,
                status='PROCESSING',
                progress=progress,
                result=task_result.info if isinstance(task_result.info, dict) else None,
                error=None
            )
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            # 存储结果到Redis，设置1天过期时间
            redis_client.setex(f"task_result:{task_id}", 3600 * 24, json.dumps(result))

            return TaskStatusResponse(
                task_id=task_id,
                status='SUCCESS',
                progress=100,
                result={
                    'success': result.get('success', False),
                    'title': result.get('title'),
                    'file_size': result.get('file_size')
                },
                error=None
            )
        elif task_result.state == 'FAILURE':
            return TaskStatusResponse(
                task_id=task_id,
                status='FAILURE',
                progress=0,
                result=None,
                error=str(task_result.info) if task_result.info else "任务执行失败"
            )
        else:
            return TaskStatusResponse(
                task_id=task_id,
                status=task_result.state,
                progress=progress,
                result=task_result.info if isinstance(task_result.info, dict) else None,
                error=None
            )

    except Exception as e:
        return TaskStatusResponse(
            task_id=task_id,
            status='ERROR',
            progress=0,
            result=None,
            error=str(e)
        )

@router.get("/task/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(
    task_id: str,
    request_obj: Request,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    获取任务结果（HTML内容）

    只有当任务状态为SUCCESS时才能获取到HTML内容
    """
    try:
        # 首先尝试从Redis获取结果
        redis_key = f"task_result:{task_id}"
        cached_result = redis_client.get(redis_key)

        if cached_result:
            result = json.loads(cached_result)
            return TaskResultResponse(
                task_id=task_id,
                success=result.get('success', False),
                content=result.get('content'),
                file_size=result.get('file_size'),
                title=result.get('title'),
                error=result.get('error')
            )

        # 如果Redis中没有，尝试从Celery获取
        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.state == 'SUCCESS':
            result = task_result.result
            # 存储结果到Redis
            redis_client.setex(redis_key, 3600*24, json.dumps(result))

            return TaskResultResponse(
                task_id=task_id,
                success=result.get('success', False),
                content=result.get('content'),
                file_size=result.get('file_size'),
                title=result.get('title'),
                error=result.get('error')
            )
        elif task_result.state == 'PENDING':
            raise HTTPException(status_code=425, detail="任务尚未完成，请稍后重试")
        elif task_result.state == 'PROCESSING':
            raise HTTPException(status_code=425, detail="任务处理中，请稍后重试")
        elif task_result.state == 'FAILURE':
            error_msg = str(task_result.info) if task_result.info else "任务执行失败"
            return TaskResultResponse(
                task_id=task_id,
                success=False,
                content=None,
                file_size=None,
                title=None,
                error=error_msg
            )
        else:
            raise HTTPException(status_code=425, detail=f"任务状态: {task_result.state}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}")

# 已移除同步下载接口，只支持异步处理以提高并发性能
# 使用 POST /submit + GET /task/{task_id}/status + GET /task/{task_id}/result
