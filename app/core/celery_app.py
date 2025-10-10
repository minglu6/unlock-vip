"""
Celery 配置和实例
"""
from celery import Celery
from app.core.config import settings

# 构建 Redis URL (包含密码)
def get_redis_url():
    """生成 Redis 连接 URL"""
    if settings.REDIS_PASSWORD:
        # 带密码的 Redis URL
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    else:
        # 无密码的 Redis URL
        return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

REDIS_URL = get_redis_url()

# 创建 Celery 实例
celery_app = Celery(
    "unlock_vip",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.article_tasks', 'app.tasks.cleanup_tasks']  # 添加清理任务模块
)

# Celery 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    result_expires=3600,  # 结果保留1小时
    worker_prefetch_multiplier=1,  # 每次只预取一个任务
    worker_max_tasks_per_child=50,  # 每个worker处理50个任务后重启
    task_default_queue='celery',  # 默认队列
    task_routes={
        'tasks.download_and_save_article': {'queue': 'celery'},
        'tasks.cleanup_old_downloads': {'queue': 'celery'},
        'tasks.get_downloads_stats': {'queue': 'celery'},
    },
    # 定时任务配置
    beat_schedule={
        'cleanup-old-downloads-daily': {
            'task': 'tasks.cleanup_old_downloads',
            'schedule': 86400.0,  # 每24小时执行一次（秒）
            'args': (7, False),  # 删除7天前的文件，不是演练模式
            'options': {'queue': 'celery'}
        },
    }
)
