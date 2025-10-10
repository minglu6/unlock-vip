"""
Celery 任务模块
"""
from .article_tasks import download_and_save_article

__all__ = ['download_and_save_article']
