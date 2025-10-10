"""
文章下载的 Celery 异步任务
"""
import logging
from app.core.celery_app import celery_app
from app.services.article_service import ArticleService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='tasks.download_and_save_article')
def download_and_save_article(self, url: str):
    """
    异步下载并保存CSDN文章为HTML文件
    
    Args:
        url: 文章URL

    Returns:
        dict: 包含file_path、file_size、title的字典
    """
    try:
        # 更新任务状态为进行中
        self.update_state(state='PROCESSING', meta={'status': '正在处理文章下载...'})
        
        logger.info(f"开始处理任务: {self.request.id}, URL: {url}")
        
        # 创建文章服务实例
        article_service = ArticleService()
        
        # 下载并保存文章
        result = article_service.save_article(url)
        
        # 读取HTML文件内容
        with open(result['file_path'], 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 清理资源
        article_service.close()
        
        logger.info(f"任务完成: {self.request.id}, 文件大小: {result['file_size']} 字节")
        
        return {
            'success': True,
            'content': html_content,
            'file_size': result['file_size'],
            'title': result['title'],
            'error': None
        }
        
    except Exception as e:
        logger.error(f"任务失败: {self.request.id}, 错误: {str(e)}")
        return {
            'success': False,
            'content': None,
            'file_size': None,
            'title': None,
            'error': str(e)
        }
