# 🧹 自动文件清理系统

## 概述

为了防止下载的 HTML 文件无限累积占用磁盘空间，系统实现了自动文件清理功能。

## 功能特性

- ✅ **自动定时清理** - 每24小时自动执行一次
- ✅ **可配置保留期** - 默认保留7天，可自定义
- ✅ **演练模式** - 可以先预览将删除哪些文件
- ✅ **手动触发** - 支持通过 API 手动清理
- ✅ **统计信息** - 查看下载目录的详细统计
- ✅ **清理日志** - 记录每次清理的详细信息

## 配置说明

### 环境变量

在 `.env` 文件中配置：

```bash
# 文件保留天数（默认7天）
CLEANUP_RETENTION_DAYS=7

# 是否启用自动清理（默认true）
CLEANUP_ENABLED=true
```

### 定时任务配置

系统默认配置：
- **执行频率**: 每24小时
- **保留天数**: 7天（可配置）
- **时区**: Asia/Shanghai
- **队列**: celery

修改定时任务需要编辑 `app/core/celery_app.py`。

## 使用方法

### 1. 启动定时任务服务

除了 Worker，还需要启动 Celery Beat（调度器）：

```bash
# 启动 Worker
celery -A app.core.celery_app worker --loglevel=info -P solo --pool=solo

# 启动 Beat（新终端）
celery -A app.core.celery_app beat --loglevel=info
```

### 2. 查看下载目录统计

```bash
curl -H "X-Admin-Key: your_admin_key" \
  http://localhost:8000/api/admin/cleanup/stats
```

**响应示例：**

```json
{
  "total_files": 15,
  "total_size": 2048576,
  "total_size_formatted": "2.00 MB",
  "files_by_age": {
    "within_1_day": 2,
    "within_7_days": 5,
    "within_30_days": 6,
    "over_30_days": 2
  },
  "oldest_file": {
    "name": "old_article.html",
    "age_days": 45.3,
    "size": 15234,
    "size_formatted": "14.88 KB"
  },
  "newest_file": {
    "name": "new_article.html",
    "age_days": 0.5,
    "size": 12345,
    "size_formatted": "12.06 KB"
  },
  "largest_file": {
    "name": "large_article.html",
    "age_days": 10.2,
    "size": 524288,
    "size_formatted": "512.00 KB"
  }
}
```

### 3. 演练模式清理（预览）

在实际删除前，先查看将删除哪些文件：

```bash
# 查看7天前的文件
curl -X POST "http://localhost:8000/api/admin/cleanup/run?days=7&dry_run=true" \
  -H "X-Admin-Key: your_admin_key"

# 查看30天前的文件
curl -X POST "http://localhost:8000/api/admin/cleanup/run?days=30&dry_run=true" \
  -H "X-Admin-Key: your_admin_key"
```

**响应示例：**

```json
{
  "success": true,
  "dry_run": true,
  "retention_days": 7,
  "scanned_files": 15,
  "deleted_files": 3,
  "deleted_size": 45678,
  "kept_files": 12,
  "kept_size": 2002898,
  "errors": [],
  "deleted_list": [
    {
      "name": "old_article_1.html",
      "age_days": 10.5,
      "size": 15234,
      "size_formatted": "14.88 KB"
    },
    {
      "name": "old_article_2.html",
      "age_days": 8.2,
      "size": 20444,
      "size_formatted": "19.96 KB"
    }
  ],
  "timestamp": "2025-10-02T15:30:00"
}
```

### 4. 实际清理

确认后，执行实际删除：

```bash
# 删除7天前的文件
curl -X POST "http://localhost:8000/api/admin/cleanup/run?days=7&dry_run=false" \
  -H "X-Admin-Key: your_admin_key"

# 删除30天前的文件（更保守）
curl -X POST "http://localhost:8000/api/admin/cleanup/run?days=30&dry_run=false" \
  -H "X-Admin-Key: your_admin_key"
```

### 5. 查看清理配置

```bash
curl -H "X-Admin-Key: your_admin_key" \
  http://localhost:8000/api/admin/cleanup/config
```

**响应示例：**

```json
{
  "enabled": true,
  "retention_days": 7,
  "schedule": "每24小时执行一次",
  "timezone": "Asia/Shanghai"
}
```

## Python 示例

### 查看统计

```python
import requests
import os

ADMIN_KEY = os.getenv("ADMIN_MASTER_KEY")
BASE_URL = "http://localhost:8000"

# 获取统计信息
response = requests.get(
    f"{BASE_URL}/api/admin/cleanup/stats",
    headers={"X-Admin-Key": ADMIN_KEY}
)

stats = response.json()
print(f"总文件: {stats['total_files']}")
print(f"总大小: {stats['total_size_formatted']}")
print(f"超过30天的文件: {stats['files_by_age']['over_30_days']}")
```

### 执行清理

```python
# 演练模式
response = requests.post(
    f"{BASE_URL}/api/admin/cleanup/run",
    headers={"X-Admin-Key": ADMIN_KEY},
    params={"days": 7, "dry_run": True}
)

result = response.json()
print(f"将删除 {result['deleted_files']} 个文件")
print(f"将释放 {result['deleted_size']} 字节")

# 确认后实际删除
if result['deleted_files'] > 0:
    confirm = input("确认删除？(yes/no): ")
    if confirm.lower() == 'yes':
        response = requests.post(
            f"{BASE_URL}/api/admin/cleanup/run",
            headers={"X-Admin-Key": ADMIN_KEY},
            params={"days": 7, "dry_run": False}
        )
        print("清理完成！")
```

## Docker 部署

### docker-compose.yml

添加 Celery Beat 服务：

```yaml
services:
  # ... 其他服务 ...
  
  celery-beat:
    build: .
    command: celery -A app.core.celery_app beat --loglevel=info
    volumes:
      - ./downloads:/app/downloads
    environment:
      - REDIS_HOST=redis
      - DATABASE_HOST=mysql
      - CLEANUP_RETENTION_DAYS=7
      - CLEANUP_ENABLED=true
    depends_on:
      - redis
      - mysql
    networks:
      - unlock-vip-network
```

### 启动服务

```bash
docker-compose up -d celery-beat
```

## 监控和日志

### Celery Beat 日志

查看定时任务调度日志：

```bash
# Docker
docker-compose logs -f celery-beat

# 本地
tail -f celery-beat.log
```

### Worker 日志

清理任务执行时会在 Worker 日志中记录：

```
[2025-10-02 15:30:00] INFO: 开始清理任务: 保留 7 天内的文件
[2025-10-02 15:30:01] INFO: 已删除: old_article.html (年龄: 10.5天, 大小: 14.88 KB)
[2025-10-02 15:30:02] INFO: 清理完成: 扫描 15 个文件, 已删除 3 个 (45.67 KB), 保留 12 个 (1.95 MB)
```

## 最佳实践

### 保留策略建议

| 场景 | 建议保留天数 | 说明 |
|------|-------------|------|
| 开发测试 | 1-3天 | 快速清理，节省空间 |
| 生产环境 | 7-14天 | 平衡存储和可追溯性 |
| 归档需求 | 30-90天 | 需要长期保留下载记录 |

### 定时任务频率

| 频率 | 配置 | 适用场景 |
|------|------|---------|
| 每小时 | `3600.0` | 下载量大，磁盘紧张 |
| 每天凌晨 | `crontab='0 2 * * *'` | 推荐，影响小 |
| 每周 | `crontab='0 2 * * 0'` | 下载量小 |

### 磁盘空间监控

建议设置告警：

```python
# 监控脚本示例
import requests

response = requests.get(f"{BASE_URL}/api/admin/cleanup/stats", ...)
stats = response.json()

# 告警阈值
if stats['total_size'] > 1024 * 1024 * 1024:  # 1GB
    send_alert(f"下载目录已达 {stats['total_size_formatted']}")

if stats['files_by_age']['over_30_days'] > 100:
    send_alert(f"有 {stats['files_by_age']['over_30_days']} 个文件超过30天")
```

## 故障排查

### 问题：定时任务没有执行

**检查项：**
1. Celery Beat 是否正在运行
2. Redis 连接是否正常
3. 检查 Beat 日志

**解决：**
```bash
# 检查 Beat 状态
ps aux | grep "celery beat"

# 重启 Beat
docker-compose restart celery-beat
```

### 问题：清理任务失败

**检查项：**
1. 下载目录权限
2. 文件是否被占用
3. 查看 Worker 日志

**解决：**
```bash
# 检查目录权限
ls -la downloads/

# 手动触发（查看详细错误）
curl -X POST "http://localhost:8000/api/admin/cleanup/run?dry_run=true" \
  -H "X-Admin-Key: $ADMIN_KEY"
```

### 问题：误删除重要文件

**预防措施：**
1. 始终先用演练模式
2. 设置合理的保留天数
3. 定期备份重要文件

**恢复方案：**
- 如果有备份，从备份恢复
- 查看请求日志，重新下载文章

## 高级配置

### 自定义清理条件

编辑 `app/tasks/cleanup_tasks.py`，可以添加自定义清理逻辑：

```python
# 示例：按文件大小清理
def cleanup_by_size(max_size_mb: int = 100):
    """清理超过指定大小的文件"""
    # ... 实现代码
```

### 多目录清理

如果需要清理多个目录：

```python
# 在 cleanup_tasks.py 中
CLEANUP_DIRS = [
    "downloads",
    "temp",
    "cache"
]
```

### Webhook 通知

清理完成后发送通知：

```python
# 在清理任务中添加
if result["deleted_files"] > 0:
    send_webhook({
        "message": f"已清理 {result['deleted_files']} 个文件",
        "size": result["deleted_size"]
    })
```

## API 接口汇总

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/cleanup/stats` | GET | 获取统计信息 |
| `/api/admin/cleanup/run` | POST | 执行清理 |
| `/api/admin/cleanup/config` | GET | 获取配置 |
| `/api/admin/cleanup/config` | PUT | 更新配置 |

所有接口都需要 `X-Admin-Key` header。

## 相关文档

- [管理员安全指南](ADMIN_SECURITY.md)
- [API 认证文档](API_AUTHENTICATION.md)
- [Docker 部署指南](DOCKER_DEPLOYMENT.md)

---

**版本**: 1.0  
**更新时间**: 2025-10-02
