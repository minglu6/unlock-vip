from fastapi import APIRouter, HTTPException
from app.models.schemas import ArticleRequest, ArticleResponse
from app.services.article_service import ArticleService
from urllib.parse import urlparse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_CSDN_DOMAINS = ['blog.csdn.net', 'wenku.csdn.net']
ALLOWED_SCHEMES = {'http', 'https'}


@router.post("/download", response_model=ArticleResponse)
async def download_article(request: ArticleRequest):
    """
    下载CSDN文章/文档（同步接口）

    直接返回HTML内容，不使用异步任务队列

    Args:
        request: 包含url的请求对象

    Returns:
        ArticleResponse: 包含HTML内容、标题、文件大小等信息
    """
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
        error_detail = '请提供有效的CSDN博客文章或文库文档链接'
        raise HTTPException(status_code=400, detail=error_detail)

    try:
        logger.info(f"开始下载文章: {url}")

        # 创建文章服务实例
        article_service = ArticleService()

        # 下载文章
        article_data = article_service.download_article(url)

        # 提取纯净内容
        clean_html = article_service.extract_clean_content(
            article_data['html'],
            article_data.get('title', '未知标题'),
            url
        )

        # 清理资源
        article_service.close()

        logger.info(f"文章下载成功: {article_data.get('title')}")

        return ArticleResponse(
            success=True,
            content=clean_html,
            file_size=len(clean_html.encode('utf-8')),
            title=article_data.get('title'),
            error=None
        )

    except Exception as e:
        logger.error(f"下载文章失败: {str(e)}")
        article_service.close()
        return ArticleResponse(
            success=False,
            content=None,
            file_size=None,
            title=None,
            error=str(e)
        )
