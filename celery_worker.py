"""
Celery Worker 启动脚本
用于启动 Celery worker 来处理异步任务
"""
from app.core.celery_app import celery_app

if __name__ == '__main__':
    # 启动 worker
    # 使用命令行: celery -A celery_worker.celery_app worker --loglevel=info -P solo
    celery_app.start()
