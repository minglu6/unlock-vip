# 🔔 Celery Beat 定时任务启动指南

## 什么是 Celery Beat？

Celery Beat 是 Celery 的任务调度器，用于按计划执行定时任务（类似 Linux 的 cron）。

在我们的系统中，Beat 负责：
- ⏰ 每24小时自动执行文件清理任务
- 📊 定期生成统计报告（可选）
- 🔄 其他需要定期执行的任务

## 快速启动

### Windows 本地开发

需要开启 **3个终端**：

**终端 1 - Redis**
```powershell
docker start unlock-vip-redis
```

**终端 2 - Celery Worker**
```powershell
celery -A app.core.celery_app worker --loglevel=info -P solo --pool=solo
```

**终端 3 - Celery Beat（新增）**
```powershell
celery -A app.core.celery_app beat --loglevel=info
```

### Linux/Mac 本地开发

```bash
# 终端 1: Redis
docker start unlock-vip-redis

# 终端 2: Worker
celery -A app.core.celery_app worker --loglevel=info

# 终端 3: Beat
celery -A app.core.celery_app beat --loglevel=info
```

## Docker 部署

### 1. 更新 docker-compose.yml

添加 Beat 服务：

```yaml
services:
  # ... 现有服务 ...
  
  celery-beat:
    build: .
    command: celery -A app.core.celery_app beat --loglevel=info
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
    environment:
      - REDIS_HOST=redis
      - DATABASE_HOST=mysql
      - DATABASE_PORT=3306
      - DATABASE_USER=${DATABASE_USER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_NAME=${DATABASE_NAME}
      - CLEANUP_RETENTION_DAYS=${CLEANUP_RETENTION_DAYS:-7}
      - CLEANUP_ENABLED=${CLEANUP_ENABLED:-true}
    depends_on:
      - redis
      - mysql
    networks:
      - unlock-vip-network
    restart: unless-stopped
```

### 2. 启动服务

```bash
# 启动所有服务（包括 Beat）
docker-compose up -d

# 或只启动 Beat
docker-compose up -d celery-beat

# 查看 Beat 日志
docker-compose logs -f celery-beat
```

## 验证 Beat 是否运行

### 检查进程

**Windows:**
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*celery*"}
```

**Linux/Mac:**
```bash
ps aux | grep "celery beat"
```

### 查看日志

Beat 启动后会显示：

```
celery beat v5.4.0 is starting.
__    -    ... __   -        _
LocalTime -> 2025-10-02 15:30:00
Configuration ->
    . broker -> redis://localhost:6379/0
    . scheduler -> celery.beat.PersistentScheduler
    . db -> celerybeat-schedule
    . loader -> celery.loaders.app.AppLoader

Scheduler: Sending due task cleanup-old-downloads-daily
```

### 测试定时任务

**查看已注册的定时任务：**

```bash
# Windows
celery -A app.core.celery_app inspect scheduled

# 查看 Beat 配置
celery -A app.core.celery_app beat --help
```

## 定时任务配置

当前配置在 `app/core/celery_app.py`：

```python
beat_schedule={
    'cleanup-old-downloads-daily': {
        'task': 'tasks.cleanup_old_downloads',
        'schedule': 86400.0,  # 每24小时（秒）
        'args': (7, False),  # 删除7天前的文件，实际删除
        'options': {'queue': 'celery'}
    },
}
```

### 修改执行频率

**每小时执行：**
```python
'schedule': 3600.0,  # 3600秒 = 1小时
```

**每天凌晨2点执行（推荐）：**
```python
from celery.schedules import crontab

'schedule': crontab(hour=2, minute=0),  # 02:00
```

**每周日凌晨执行：**
```python
'schedule': crontab(hour=2, minute=0, day_of_week=0),  # 周日 02:00
```

**每月1号执行：**
```python
'schedule': crontab(hour=2, minute=0, day_of_month=1),  # 每月1号 02:00
```

### 添加新的定时任务

在 `beat_schedule` 中添加：

```python
beat_schedule={
    'cleanup-old-downloads-daily': {
        'task': 'tasks.cleanup_old_downloads',
        'schedule': 86400.0,
        'args': (7, False),
    },
    # 新任务：每小时统计一次
    'stats-hourly': {
        'task': 'tasks.get_downloads_stats',
        'schedule': 3600.0,  # 每小时
        'options': {'queue': 'celery'}
    },
}
```

## 常见问题

### Q: Beat 可以和 Worker 在同一个进程吗？

**不推荐**。虽然可以使用 `celery worker -B`，但生产环境建议分开：

```bash
# ❌ 不推荐（开发快速测试可以）
celery -A app.core.celery_app worker -B --loglevel=info

# ✅ 推荐（生产环境）
celery -A app.core.celery_app worker --loglevel=info  # 终端1
celery -A app.core.celery_app beat --loglevel=info    # 终端2
```

### Q: Beat 需要数据库吗？

Beat 使用 `celerybeat-schedule` 文件存储调度信息（本地文件，不是数据库）。

### Q: 如何查看下次执行时间？

查看 Beat 日志：

```
Scheduler: Sending due task cleanup-old-downloads-daily
Next run at: 2025-10-03 02:00:00+08:00
```

### Q: 手动触发定时任务？

定时任务也可以手动触发：

```python
from app.tasks.cleanup_tasks import cleanup_old_downloads

# 同步执行
result = cleanup_old_downloads(days=7, dry_run=False)

# 异步执行
task = cleanup_old_downloads.delay(days=7, dry_run=False)
```

或通过 API：

```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/run?days=7" \
  -H "X-Admin-Key: your_admin_key"
```

### Q: Beat 挂了怎么办？

Beat 挂了不影响手动触发任务，只是自动调度会停止。

**检查：**
```bash
# 检查 Beat 状态
docker-compose ps celery-beat

# 查看日志
docker-compose logs --tail=100 celery-beat
```

**重启：**
```bash
docker-compose restart celery-beat
```

### Q: 可以有多个 Beat 进程吗？

**不可以**！同一个 Celery 应用只能有一个 Beat 进程，否则会重复执行任务。

如果需要高可用，使用 `celery-beat-scheduler` 或 Redis 作为调度器。

## 监控 Beat

### Flower 监控

访问 Flower 可以看到定时任务：

```bash
# 启动 Flower
celery -A app.core.celery_app flower --port=5555

# 访问
http://localhost:5555
```

在 Flower 中可以看到：
- 已注册的定时任务
- 下次执行时间
- 历史执行记录

### 日志监控

Beat 日志示例：

```
[2025-10-02 02:00:00] INFO: Scheduler: Sending due task cleanup-old-downloads-daily
[2025-10-02 02:00:01] INFO: Task cleanup-old-downloads-daily[uuid] sent
[2025-10-02 02:00:05] INFO: Task cleanup-old-downloads-daily[uuid] succeeded in 4.2s
```

Worker 日志会显示任务执行：

```
[2025-10-02 02:00:01] INFO: Task tasks.cleanup_old_downloads[uuid] received
[2025-10-02 02:00:01] INFO: 开始清理任务: 保留 7 天内的文件
[2025-10-02 02:00:05] INFO: 清理完成: 已删除 5 个文件 (1.2 MB)
[2025-10-02 02:00:05] INFO: Task tasks.cleanup_old_downloads[uuid] succeeded
```

## 生产环境建议

### 使用 systemd（Linux）

创建 `/etc/systemd/system/celery-beat.service`:

```ini
[Unit]
Description=Celery Beat Service
After=network.target redis.service mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/unlock-vip
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A app.core.celery_app beat --loglevel=info
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-beat
sudo systemctl start celery-beat
sudo systemctl status celery-beat
```

### 使用 Supervisor（Linux/Mac）

配置 `/etc/supervisor/conf.d/celery-beat.conf`:

```ini
[program:celery-beat]
command=/path/to/venv/bin/celery -A app.core.celery_app beat --loglevel=info
directory=/path/to/unlock-vip
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-beat.log
```

### 使用 PM2（Windows/Linux/Mac）

```bash
# 安装 PM2
npm install -g pm2

# 启动 Beat
pm2 start "celery -A app.core.celery_app beat --loglevel=info" --name celery-beat

# 查看状态
pm2 status celery-beat

# 查看日志
pm2 logs celery-beat

# 开机自启
pm2 save
pm2 startup
```

## 故障排查清单

- [ ] Redis 是否正常运行
- [ ] Worker 是否正常运行
- [ ] Beat 进程是否存在
- [ ] 检查 Beat 日志是否有错误
- [ ] 检查 `celerybeat-schedule` 文件权限
- [ ] 检查时区配置是否正确
- [ ] 验证任务是否在 beat_schedule 中注册

## 相关命令

```bash
# 查看所有定时任务
celery -A app.core.celery_app inspect scheduled

# 查看活跃任务
celery -A app.core.celery_app inspect active

# 查看已注册任务
celery -A app.core.celery_app inspect registered

# 清理 Beat 调度数据（谨慎）
rm celerybeat-schedule
```

---

**版本**: 1.0  
**更新时间**: 2025-10-02  
**相关文档**: [文件清理文档](FILE_CLEANUP.md)
