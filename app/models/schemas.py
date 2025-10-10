from pydantic import BaseModel, HttpUrl
from typing import Optional
import uuid

# ===== 统一的文章请求和响应模型 =====
class ArticleRequest(BaseModel):
    """文章下载请求"""
    url: str

class ArticleResponse(BaseModel):
    """文章下载响应"""
    success: bool
    content: Optional[str] = None  # HTML内容
    file_size: Optional[int] = None  # 文件大小（字节）
    title: Optional[str] = None  # 文章标题
    error: Optional[str] = None

class TaskSubmissionResponse(BaseModel):
    """任务提交响应"""
    task_id: str  # UUID格式的任务ID
    status: str  # 任务初始状态，通常为PENDING
    message: str  # 提示信息

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str  # PENDING, PROCESSING, SUCCESS, FAILURE
    progress: Optional[int] = None  # 进度百分比 (0-100)
    result: Optional[dict] = None  # 任务结果
    error: Optional[str] = None

class TaskResultResponse(BaseModel):
    """任务结果响应"""
    task_id: str
    success: bool
    content: Optional[str] = None  # HTML文件内容
    file_size: Optional[int] = None  # 文件大小（字节）
    title: Optional[str] = None  # 文章标题
    error: Optional[str] = None