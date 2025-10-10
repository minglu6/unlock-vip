# 🐳 Docker 部署指南

本文档说明如何使用 Docker 和 Docker Compose 部署 Unlock-VIP 服务。

## 📋 前置要求

- Docker Engine 20.10+
- Docker Compose V2 或 docker-compose 1.29+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

## 🚀 快速开始

### 1. 准备配置文件

```bash
# 复制环境变量模板
cp .env.docker .env

# 编辑配置文件
# 至少需要修改以下配置：
# - DATABASE_PASSWORD
# - CSDN_USERNAME
# - CSDN_PASSWORD
```

### 2. 启动服务

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows PowerShell:**
```powershell
.\deploy.ps1
```

**或者手动启动:**
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 初始化数据库
docker-compose exec web python manage_db.py init

# 创建第一个 API Key
docker-compose exec web python manage_db.py create "我的密钥"
```

### 3. 访问服务

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Flower 监控**: http://localhost:5555 (默认账号: admin/admin123)

## 🏗️ 服务架构

Docker Compose 部署包含以下服务：

```
┌─────────────┐
│   MySQL     │  数据库 (端口: 3306)
└─────────────┘
       │
┌─────────────┐
│   Redis     │  消息队列 (端口: 6379)
└─────────────┘
       │
┌─────────────┐
│     Web     │  FastAPI 应用 (端口: 8000)
└─────────────┘
       │
┌─────────────┐
│   Celery    │  异步任务处理
└─────────────┘
       │
┌─────────────┐
│   Flower    │  监控面板 (端口: 5555)
└─────────────┘
```

## 📁 目录结构

```
.
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile              # Docker 镜像定义
├── .env                    # 环境变量（需要创建）
├── .env.docker            # 环境变量模板
├── init-db.sql            # MySQL 初始化脚本
├── deploy.sh              # Linux/Mac 部署脚本
├── deploy.ps1             # Windows 部署脚本
├── downloads/             # 文章下载目录（自动创建）
├── logs/                  # 日志目录（自动创建）
└── cookies.json           # CSDN Cookies（可选）
```

## 🔧 配置说明

### 环境变量

编辑 `.env` 文件配置以下参数：

```env
# 数据库配置
DATABASE_HOST=mysql              # 容器内使用服务名
DATABASE_PORT=3306
DATABASE_USER=unlock_vip
DATABASE_PASSWORD=your_password  # ⚠️ 必须修改
DATABASE_NAME=unlock_vip

# Redis 配置
REDIS_HOST=redis                 # 容器内使用服务名
REDIS_PORT=6379
REDIS_DB=0

# CSDN 账号
CSDN_USERNAME=your_username      # ⚠️ 必须修改
CSDN_PASSWORD=your_password      # ⚠️ 必须修改

# Flower 监控
FLOWER_USER=admin
FLOWER_PASSWORD=admin123         # ⚠️ 建议修改
```

### 端口映射

默认端口映射：

- `8000:8000` - FastAPI Web 服务
- `3306:3306` - MySQL 数据库
- `6379:6379` - Redis
- `5555:5555` - Flower 监控

如需修改，编辑 `docker-compose.yml` 中的 `ports` 配置。

## 🛠️ 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f web
docker-compose logs -f celery
```

### 数据库管理

```bash
# 初始化数据库
docker-compose exec web python manage_db.py init

# 创建 API Key
docker-compose exec web python manage_db.py create "密钥名称"

# 列出所有 API Keys
docker-compose exec web python manage_db.py list

# 查看统计信息
docker-compose exec web python manage_db.py stats

# 直接连接 MySQL
docker-compose exec mysql mysql -u unlock_vip -p unlock_vip
```

### 容器管理

```bash
# 进入容器 Shell
docker-compose exec web bash
docker-compose exec celery bash

# 查看容器资源使用
docker stats

# 重新构建镜像
docker-compose build --no-cache

# 清理未使用的镜像
docker system prune -a
```

### 备份和恢复

```bash
# 备份数据库
docker-compose exec mysql mysqldump -u unlock_vip -p unlock_vip > backup.sql

# 恢复数据库
docker-compose exec -T mysql mysql -u unlock_vip -p unlock_vip < backup.sql

# 备份卷数据
docker run --rm -v unlock-vip_mysql_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mysql_backup.tar.gz -C /data .
```

## 📊 监控和调试

### Flower 监控面板

访问 http://localhost:5555 查看：

- 实时任务状态
- Worker 健康状况
- 任务执行历史
- 任务执行时间统计

默认账号: `admin` / `admin123`

### 日志查看

```bash
# 实时查看所有日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100

# 只查看错误日志
docker-compose logs | grep ERROR
```

### 健康检查

```bash
# 检查 API 健康
curl http://localhost:8000/health

# 检查所有服务健康状态
docker-compose ps
```

## 🔒 安全建议

### 生产环境部署

1. **修改默认密码**
   ```env
   DATABASE_PASSWORD=strong_password_here
   REDIS_PASSWORD=redis_password_here
   FLOWER_PASSWORD=flower_password_here
   ```

2. **限制端口暴露**
   ```yaml
   # 不对外暴露数据库端口
   mysql:
     ports:
       - "127.0.0.1:3306:3306"  # 仅本地访问
   ```

3. **使用 HTTPS**
   - 配置 Nginx 反向代理
   - 使用 Let's Encrypt 免费证书

4. **保护管理接口**
   - 为管理 API 添加额外认证
   - 使用防火墙限制访问

5. **定期备份**
   - 设置自动备份脚本
   - 异地存储备份数据

## 🐛 故障排查

### 服务无法启动

```bash
# 查看详细错误日志
docker-compose logs web

# 检查容器状态
docker-compose ps

# 检查健康状态
docker inspect unlock-vip-api | grep -A 10 Health
```

### 数据库连接失败

```bash
# 检查 MySQL 是否就绪
docker-compose exec mysql mysqladmin ping -h localhost

# 检查数据库是否创建
docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"

# 测试连接
docker-compose exec web python -c "from app.db.database import engine; engine.connect()"
```

### Celery Worker 不工作

```bash
# 检查 Worker 状态
docker-compose exec celery celery -A app.core.celery_app inspect active

# 检查 Redis 连接
docker-compose exec redis redis-cli ping

# 重启 Worker
docker-compose restart celery
```

### 端口冲突

```bash
# 查看端口占用
netstat -an | grep 8000
netstat -an | grep 3306

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8001:8000"  # 改为其他端口
```

## 📈 性能优化

### 资源限制

编辑 `docker-compose.yml` 添加资源限制：

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Celery 并发

```yaml
celery:
  command: celery -A app.core.celery_app worker --loglevel=info --concurrency=8
```

### 数据库优化

```yaml
mysql:
  command: >
    --default-authentication-plugin=mysql_native_password
    --max-connections=200
    --innodb-buffer-pool-size=1G
```

## 🔄 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 停止服务
docker-compose down

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d

# 5. 检查健康状态
docker-compose ps
docker-compose logs -f
```

## 📚 相关文档

- [README.md](../README.md) - 项目主文档
- [API_AUTHENTICATION.md](API_AUTHENTICATION.md) - API 认证说明
- [DEPLOYMENT.md](DEPLOYMENT.md) - 传统部署方式

## 💡 提示

1. **首次启动较慢**: 需要下载镜像和构建，请耐心等待
2. **数据持久化**: MySQL 和 Redis 数据存储在 Docker 卷中
3. **日志管理**: 建议配置日志轮转避免占用过多空间
4. **监控告警**: 生产环境建议配置监控和告警系统

## 🆘 获取帮助

遇到问题？

1. 查看日志: `docker-compose logs -f`
2. 检查环境变量配置
3. 确认所有依赖服务正常运行
4. 查看 [故障排查](#-故障排查) 章节
