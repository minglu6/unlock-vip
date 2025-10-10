# 🚀 部署文件清单和说明

## 📦 部署相关文件总览

### 核心部署文件

| 文件                        | 位置   | 说明                   | 必需  |
| --------------------------- | ------ | ---------------------- | ----- |
| `docker-compose.prod.yml` | 根目录 | 生产环境Docker编排配置 | ✅ 是 |
| `Dockerfile`              | 根目录 | Docker镜像构建文件     | ✅ 是 |
| `.env.prod.example`       | 根目录 | 生产环境配置模板       | ✅ 是 |
| `cookies.json`            | 根目录 | CSDN登录状态           | ✅ 是 |
| `requirements.txt`        | 根目录 | Python依赖列表         | ✅ 是 |
| `deploy-production.sh`    | 根目录 | 一键部署脚本           | 推荐  |
| `pre-deploy-check.sh`     | 根目录 | 部署前检查脚本         | 推荐  |

### 应用代码

| 目录/文件            | 说明           |
| -------------------- | -------------- |
| `app/`             | 应用主目录     |
| ├─`main.py`      | FastAPI主应用  |
| ├─`api/`         | API端点        |
| ├─`services/`    | 业务逻辑服务   |
| ├─`db/`          | 数据库模型     |
| ├─`middleware/`  | 中间件         |
| └─`core/`        | 核心配置       |
| `celery_worker.py` | Celery工作进程 |
| `run.py`           | 应用启动入口   |

### 配置文件

| 文件                             | 说明             |
| -------------------------------- | ---------------- |
| `nginx.conf`                   | Nginx配置        |
| `nginx/conf.d/unlock-vip.conf` | Nginx站点配置    |
| `mysql-conf.d/mysql.cnf`       | MySQL配置        |
| `init-db.sql`                  | 数据库初始化脚本 |

### 文档

| 文件                                 | 说明                       |
| ------------------------------------ | -------------------------- |
| `docs/ALIYUN_PRODUCTION_DEPLOY.md` | 阿里云生产环境完整部署指南 |
| `PRODUCTION_DEPLOY_README.md`      | 部署快速指南               |
| `docs/DOCKER_QUICKSTART.md`        | Docker快速部署             |
| `docs/THREAD_POOL_CONFIG.md`       | 线程池配置                 |
| `docs/FILE_DOWNLOAD_API.md`        | 文件下载API文档            |

---

## 🚀 部署步骤总结

### Step 1: 准备阶段

```bash
# 在本地运行检查
bash pre-deploy-check.sh
```

**检查项**:

- ✅ cookies.json 已准备
- ✅ .env.prod 已配置（所有密码已修改）
- ✅ Docker Compose配置正确
- ✅ 服务器满足要求

### Step 2: 服务器准备

```bash
# 连接服务器
ssh root@your-server-ip

# 安装Docker（如未安装）
curl -fsSL https://get.docker.com | bash

# 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### Step 3: 部署应用

```bash
# 克隆项目
cd /opt
git clone https://github.com/minglu6/unlock-vip.git
cd unlock-vip

# 运行一键部署（推荐）
bash deploy-production.sh

# 或手动部署
cp .env.prod.example .env.prod
# 编辑配置文件...
docker-compose -f docker-compose.prod.yml up -d
```

### Step 4: 验证部署

```bash
# 检查容器状态
docker-compose -f docker-compose.prod.yml ps

# 测试API
curl http://localhost:8000/health

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🔧 配置说明

### 必须修改的配置

在 `.env.prod` 中：

```bash
# 数据库密码（必改！）
MYSQL_ROOT_PASSWORD=your_strong_password
MYSQL_PASSWORD=your_user_password

# Redis密码（必改！）
REDIS_PASSWORD=your_redis_password

# 应用密钥（必改！使用 openssl rand -hex 32 生成）
SECRET_KEY=your_secret_key

# 管理员密钥（必改！）
ADMIN_KEY=your_admin_key
```

### 可选配置

```bash
# 性能配置
WORKERS=5                    # Gunicorn工作进程数
CELERY_WORKER_CONCURRENCY=4  # Celery并发数
DB_POOL_SIZE=5               # 数据库连接池

# 功能开关
ENABLE_DOCS=false            # 是否启用API文档
ENABLE_FILE_CLEANUP=true     # 是否启用自动清理
AUTO_BACKUP_ENABLED=true     # 是否启用自动备份

# 域名和SSL
DOMAIN=your-domain.com       # 域名（如有）
SSL_ENABLED=false            # 是否启用SSL
```

---

## 📊 服务架构

```
┌─────────────────────────────────────────┐
│          Nginx (反向代理/SSL)            │
│       Port: 80/443 → 8000              │
└────────────────┬────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│          FastAPI Application            │
│         (4个工作进程)                    │
│         Port: 8000                      │
└────────┬──────────────────┬─────────────┘
         │                  │
    ┌────┴─────┐     ┌──────┴───────┐
    │  MySQL   │     │    Redis     │
    │  Port:   │     │    Port:     │
    │  3306    │     │    6379      │
    └──────────┘     └──────┬───────┘
                            │
                     ┌──────┴───────┐
                     │    Celery    │
                     │    Worker    │
                     └──────────────┘
```

---

## 🔒 安全配置

### 1. 修改默认密码

```bash
# 生成强密码
openssl rand -hex 32

# 生成管理员密钥
docker-compose -f docker-compose.prod.yml exec app python scripts/generate_admin_key.py
```

### 2. 配置防火墙

```bash
# Ubuntu/Debian (UFW)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# CentOS/RHEL (Firewalld)
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

### 3. 配置SSL证书

```bash
# 安装Certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

### 4. 限制IP访问

在Nginx配置中添加：

```nginx
location /api/admin/ {
    allow 123.45.67.89;  # 你的IP
    deny all;
    proxy_pass http://127.0.0.1:8000;
}
```

---

## 📈 性能优化

### 根据服务器配置调整

#### 小型服务器（2核2GB）

```yaml
# docker-compose.prod.yml
app:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
  
celery:
  command: celery -A celery_worker.celery_app worker -l info --concurrency=2
```

``bash

# .env.prod

WORKERS=2
CELERY_WORKER_CONCURRENCY=2
DB_POOL_SIZE=3

```

#### 中型服务器（4核4GB）

```yaml
# docker-compose.prod.yml
app:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

celery:
  command: celery -A celery_worker.celery_app worker -l info --concurrency=4
```

```bash
# .env.prod
WORKERS=5
CELERY_WORKER_CONCURRENCY=4
DB_POOL_SIZE=5
```

#### 大型服务器（8核8GB+）

```yaml
# docker-compose.prod.yml
app:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8

celery:
  command: celery -A celery_worker.celery_app worker -l info --concurrency=8
```

```bash
# .env.prod
WORKERS=9
CELERY_WORKER_CONCURRENCY=8
DB_POOL_SIZE=10
```

### 调整线程池

修改 `app/services/file_service.py`:

```python
self._executor = ThreadPoolExecutor(
    max_workers=8,  # 根据CPU核心数调整
    thread_name_prefix="FileDownload"
)
```

---

## 🔄 运维操作

### 日常维护

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看资源使用
docker stats

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f app

# 重启服务
docker-compose -f docker-compose.prod.yml restart
```

### 更新部署

```bash
cd /opt/unlock-vip
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 备份数据

```bash
# 手动备份
docker exec unlock-vip-mysql mysqldump -u root -p unlock_vip > backup.sql

# 自动备份（已配置则每天凌晨2点执行）
/opt/backup_unlock_vip.sh
```

### 清理空间

```bash
# 清理Docker
docker system prune -a

# 清理旧文件
find /opt/unlock-vip/downloads -mtime +7 -delete

# 清理日志
find /var/log -name "*.log" -mtime +30 -delete
```

---

## 🐛 常见问题

### 1. 容器无法启动

```bash
# 查看详细错误
docker-compose -f docker-compose.prod.yml logs app

# 检查配置
docker-compose -f docker-compose.prod.yml config

# 重新构建
docker-compose -f docker-compose.prod.yml build --no-cache
```

### 2. 数据库连接失败

```bash
# 检查MySQL状态
docker-compose -f docker-compose.prod.yml ps mysql

# 进入MySQL
docker exec -it unlock-vip-mysql mysql -u root -p

# 查看用户权限
SHOW GRANTS FOR 'unlock_user'@'%';
```

### 3. Redis连接失败

```bash
# 测试Redis
docker exec -it unlock-vip-redis redis-cli

# 需要密码
docker exec -it unlock-vip-redis redis-cli -a your_redis_password
```

### 4. Celery任务不执行

```bash
# 查看Celery日志
docker-compose -f docker-compose.prod.yml logs celery

# 清空队列
docker exec -it unlock-vip-redis redis-cli -a your_password FLUSHALL

# 重启Celery
docker-compose -f docker-compose.prod.yml restart celery
```

---

## 📞 获取支持

### 文档资源

- 📘 [完整部署文档](docs/ALIYUN_PRODUCTION_DEPLOY.md)
- 📗 [快速部署指南](PRODUCTION_DEPLOY_README.md)
- 📚 [API文档](docs/README.md)
- 📦 [Postman测试集合](docs/POSTMAN_COLLECTION.json)

### 问题报告

遇到问题？

1. 查看日志：`docker-compose -f docker-compose.prod.yml logs`
2. 搜索文档：查看 `docs/` 目录
3. 提交Issue：[GitHub Issues](https://github.com/your-username/unlock-vip/issues)

---

## ✅ 部署检查清单

部署完成后，逐项确认：

- [ ] 所有容器状态为 `Up (healthy)`
- [ ] API健康检查通过 (`/health`)
- [ ] 文件服务健康检查通过 (`/api/file/health`)
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] Celery任务执行正常
- [ ] Nginx反向代理工作（如配置）
- [ ] SSL证书有效（如配置）
- [ ] 防火墙规则生效
- [ ] 备份脚本测试通过
- [ ] 监控和告警配置完成
- [ ] 所有密码已修改
- [ ] API文档可访问（或已关闭）

---

**最后更新**: 2025-10-03
**版本**: v2.0.0
**维护**: 定期检查更新，建议每周审查日志和资源使用情况
