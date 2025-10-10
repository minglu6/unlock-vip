# 阿里云 Docker 部署手册

## 📋 目录

- [服务器要求](#服务器要求)
- [部署架构](#部署架构)
- [快速部署](#快速部署)
- [详细步骤](#详细步骤)
- [镜像管理](#镜像管理)
- [监控运维](#监控运维)
- [故障排查](#故障排查)
- [安全加固](#安全加固)

---

## 🖥️ 服务器要求

### 最低配置
- **CPU**: 2核
- **内存**: 4GB
- **磁盘**: 40GB SSD
- **带宽**: 5Mbps
- **操作系统**: CentOS 7.6+ / Ubuntu 20.04+ / Alibaba Cloud Linux 3

### 推荐配置
- **CPU**: 4核
- **内存**: 8GB
- **磁盘**: 80GB SSD
- **带宽**: 10Mbps
- **操作系统**: Alibaba Cloud Linux 3

### 阿里云产品
- **ECS**: 云服务器 (推荐使用计算型 c6 或通用型 g6)
- **ACR**: 容器镜像服务 (用于私有镜像托管)
- **SLB**: 负载均衡 (可选，多实例部署时使用)
- **RDS**: 云数据库 (可选，替代自建MySQL)
- **Redis**: 云数据库 (可选，替代自建Redis)

---

## 🏗️ 部署架构

```
┌─────────────────────────────────────────────────────┐
│                  阿里云 ECS 服务器                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  Nginx (容器)                                 │  │
│  │  - 反向代理                                    │  │
│  │  - SSL 终结                                    │  │
│  │  - 负载均衡                                    │  │
│  └────────────┬─────────────────────────────────┘  │
│               │                                     │
│  ┌────────────▼─────────────────────────────────┐  │
│  │  FastAPI Web (容器)                           │  │
│  │  - 4 Worker 进程                              │  │
│  │  - RESTful API                                │  │
│  └────────────┬─────────────────────────────────┘  │
│               │                                     │
│  ┌────────────▼─────────────────────────────────┐  │
│  │  Celery Worker (容器)                         │  │
│  │  - 异步任务处理                               │  │
│  │  - 文章下载                                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  Celery Beat (容器)                           │  │
│  │  - 定时任务调度                               │  │
│  │  - 文件清理                                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────┐      ┌─────────────────────────┐ │
│  │ MySQL 8.0    │      │ Redis 7                 │ │
│  │ (容器)       │      │ (容器)                  │ │
│  └──────────────┘      └─────────────────────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  Flower (容器，可选)                          │  │
│  │  - Celery 监控                                │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 容器通信
- 所有容器在同一 Docker 网络 `unlock-vip-network`
- 服务间通过容器名称通信 (Docker DNS)
- 仅 Nginx 暴露外部端口 (80, 443)

### 数据持久化
```
/data/unlock-vip/
├── mysql/          # MySQL 数据目录
├── redis/          # Redis 持久化目录
├── downloads/      # 下载文件目录
├── logs/           # 应用日志
│   ├── app/        # FastAPI 日志
│   ├── celery/     # Celery 日志
│   └── nginx/      # Nginx 日志
├── ssl/            # SSL 证书
└── cookies.json    # CSDN Cookies
```

---

## 🚀 快速部署

### 一键部署脚本

```bash
# 1. 下载部署脚本
wget https://your-repo.com/deploy-aliyun.sh
chmod +x deploy-aliyun.sh

# 2. 执行部署
./deploy-aliyun.sh
```

部署脚本会自动完成：
- ✅ Docker 环境检查和安装
- ✅ 目录结构创建
- ✅ 配置文件生成
- ✅ 镜像拉取
- ✅ 容器启动
- ✅ 健康检查

---

## 📝 详细步骤

### 步骤 1: 准备服务器

#### 1.1 购买阿里云 ECS

1. 登录阿里云控制台
2. 选择 **云服务器 ECS**
3. 点击 **创建实例**
4. 配置选择:
   - 地域: 就近选择
   - 实例规格: ecs.c6.xlarge (4核8GB) 或更高
   - 镜像: Alibaba Cloud Linux 3.2104 LTS 64位
   - 存储: 80GB ESSD云盘
   - 网络: VPC网络，分配公网IP
   - 安全组: 开放 22, 80, 443 端口

#### 1.2 连接服务器

```bash
# 使用 SSH 连接
ssh root@your-server-ip

# 或使用阿里云控制台的 VNC 连接
```

#### 1.3 更新系统

```bash
# Alibaba Cloud Linux / CentOS
yum update -y
yum install -y wget curl vim git

# Ubuntu
apt update && apt upgrade -y
apt install -y wget curl vim git
```

### 步骤 2: 安装 Docker 环境

#### 2.1 安装 Docker

```bash
# Alibaba Cloud Linux / CentOS
yum install -y docker-ce docker-ce-cli containerd.io

# 或使用 Docker 官方脚本
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
```

#### 2.2 配置 Docker 镜像加速

```bash
# 创建配置目录
mkdir -p /etc/docker

# 配置阿里云镜像加速器
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": ["https://your-accelerator-id.mirror.aliyuncs.com"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# 重启 Docker
systemctl daemon-reload
systemctl enable docker
systemctl restart docker

# 验证安装
docker --version
docker info
```

#### 2.3 安装 Docker Compose

```bash
# 下载最新版本
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 步骤 3: 准备项目文件

#### 3.1 创建项目目录

```bash
# 创建应用目录
mkdir -p /opt/unlock-vip
cd /opt/unlock-vip

# 创建数据目录
mkdir -p /data/unlock-vip/{mysql,redis,downloads,logs,ssl}
mkdir -p /data/unlock-vip/logs/{app,celery,nginx}
```

#### 3.2 上传项目文件

**方式 A: 从 Git 仓库拉取**
```bash
git clone https://your-repo.com/unlock-vip.git /opt/unlock-vip
cd /opt/unlock-vip
```

**方式 B: 手动上传**
```bash
# 在本地打包
cd /path/to/local/unlock-vip
tar -czf unlock-vip.tar.gz \
    docker-compose.prod.yml \
    .env.prod.example \
    Dockerfile \
    nginx/ \
    mysql-conf.d/ \
    app/ \
    manage_db.py \
    requirements.txt

# 上传到服务器
scp unlock-vip.tar.gz root@your-server-ip:/opt/

# 在服务器解压
cd /opt
tar -xzf unlock-vip.tar.gz -C unlock-vip
cd unlock-vip
```

#### 3.3 配置环境变量

```bash
# 复制配置模板
cp .env.prod.example .env.prod

# 编辑配置文件
vim .env.prod
```

**必须修改的配置:**
```bash
# Docker 镜像仓库地址
DOCKER_REGISTRY=registry.cn-hangzhou.aliyuncs.com/your-namespace
VERSION=1.0.0

# 数据库密码 (强密码)
DATABASE_ROOT_PASSWORD=Abc123!@#
DATABASE_PASSWORD=Def456!@#

# Redis 密码 (强密码)
REDIS_PASSWORD=Ghi789!@#

# CSDN 账号
CSDN_USERNAME=your_csdn_username
CSDN_PASSWORD=your_csdn_password

# 验证码服务 (推荐使用 chaojiying)
CAPTCHA_SERVICE=chaojiying
CHAOJIYING_USERNAME=your_username
CHAOJIYING_PASSWORD=your_password
CHAOJIYING_SOFT_ID=your_soft_id

# 管理员密钥 (使用 generate_admin_key.py 生成)
ADMIN_MASTER_KEY=your_generated_admin_key

# Flower 监控密码
FLOWER_PASSWORD=your_flower_password
```

#### 3.4 生成 Admin Key

```bash
# 安装 Python 3
yum install -y python3

# 生成 Admin Key
python3 -c "
import secrets
import base64
key = secrets.token_urlsafe(32)
print(f'ADMIN_MASTER_KEY={key}')
"

# 将生成的 key 填入 .env.prod 文件
```

### 步骤 4: 构建和推送镜像

#### 4.1 登录阿里云容器镜像服务

```bash
# 登录 ACR
docker login --username=your-aliyun-username registry.cn-hangzhou.aliyuncs.com

# 输入密码 (阿里云容器镜像服务密码)
```

#### 4.2 构建镜像

```bash
# 构建镜像
docker build -t unlock-vip:1.0.0 .

# 打标签
docker tag unlock-vip:1.0.0 registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0
docker tag unlock-vip:1.0.0 registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:latest
```

#### 4.3 推送镜像

```bash
# 推送到阿里云容器镜像服务
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:latest
```

### 步骤 5: 配置 SSL 证书 (可选但推荐)

#### 5.1 使用 Let's Encrypt 免费证书

```bash
# 安装 certbot
yum install -y certbot

# 获取证书 (HTTP-01 验证)
certbot certonly --standalone -d your-domain.com

# 证书会生成在: /etc/letsencrypt/live/your-domain.com/

# 复制证书到项目目录
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /data/unlock-vip/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /data/unlock-vip/ssl/

# 设置权限
chmod 600 /data/unlock-vip/ssl/*.pem
```

#### 5.2 配置自动续期

```bash
# 添加定时任务
crontab -e

# 每月1号凌晨3点自动续期
0 3 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /data/unlock-vip/ssl/ && docker exec unlock-vip-nginx nginx -s reload
```

#### 5.3 修改 Nginx 配置

```bash
# 编辑 nginx/conf.d/unlock-vip.conf
vim nginx/conf.d/unlock-vip.conf

# 修改 server_name
server_name your-domain.com;
```

### 步骤 6: 启动服务

#### 6.1 使用 Docker Compose 启动

```bash
cd /opt/unlock-vip

# 使用生产配置启动
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 查看启动日志
docker-compose -f docker-compose.prod.yml logs -f
```

#### 6.2 检查服务状态

```bash
# 查看所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 应该看到所有服务都是 Up 状态
NAME                    STATUS              PORTS
unlock-vip-mysql-prod   Up (healthy)        3306/tcp
unlock-vip-redis-prod   Up (healthy)        6379/tcp
unlock-vip-api          Up (healthy)        8000/tcp
unlock-vip-celery       Up (healthy)
unlock-vip-beat         Up
unlock-vip-nginx        Up                  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
unlock-vip-flower       Up                  5555/tcp
```

#### 6.3 验证服务

```bash
# 检查健康状态
curl http://localhost/health
# 应返回: {"status":"healthy"}

# 检查 API 文档
curl http://localhost/docs
# 应返回 Swagger UI 页面

# 检查数据库连接
docker exec unlock-vip-mysql-prod mysql -uunlock_vip_user -p${DATABASE_PASSWORD} -e "SELECT 1;"
```

### 步骤 7: 初始化数据

#### 7.1 创建数据库表

```bash
# 进入 web 容器
docker exec -it unlock-vip-api bash

# 初始化数据库
python manage_db.py init

# 退出容器
exit
```

#### 7.2 生成第一个 API Key

```bash
# 使用 Admin API 生成 API Key
curl -X POST "https://your-domain.com/api/admin/keys" \
  -H "X-Admin-Key: your_admin_master_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试密钥",
    "description": "第一个API密钥",
    "rate_limit": 100,
    "expires_in_days": 365
  }'

# 保存返回的 api_key
```

### 步骤 8: 配置防火墙

#### 8.1 阿里云安全组

在阿里云控制台配置安全组规则:

| 协议 | 端口范围 | 授权对象 | 描述 |
|------|---------|---------|------|
| TCP  | 22      | 你的IP  | SSH |
| TCP  | 80      | 0.0.0.0/0 | HTTP |
| TCP  | 443     | 0.0.0.0/0 | HTTPS |

#### 8.2 服务器防火墙

```bash
# 安装 firewalld
yum install -y firewalld
systemctl start firewalld
systemctl enable firewalld

# 开放端口
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

# 查看规则
firewall-cmd --list-all
```

---

## 🗂️ 镜像管理

### 本地构建镜像

```bash
# 构建镜像
cd /opt/unlock-vip
docker build -t unlock-vip:1.0.0 .

# 测试镜像
docker run --rm unlock-vip:1.0.0 python --version
```

### 推送到阿里云 ACR

```bash
# 登录
docker login registry.cn-hangzhou.aliyuncs.com

# 打标签
docker tag unlock-vip:1.0.0 registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0

# 推送
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0
```

### 从 ACR 拉取镜像

```bash
# 拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/your-namespace/unlock-vip:1.0.0

# 查看镜像
docker images | grep unlock-vip
```

### 镜像版本管理

```bash
# 使用语义化版本
docker build -t unlock-vip:1.0.0 .
docker build -t unlock-vip:1.0.1 .
docker build -t unlock-vip:1.1.0 .

# latest 标签指向最新稳定版
docker tag unlock-vip:1.1.0 unlock-vip:latest
```

### 镜像清理

```bash
# 清理未使用的镜像
docker image prune -a -f

# 清理悬空镜像
docker image prune -f

# 查看磁盘占用
docker system df
```

---

## 📊 监控运维

### 服务监控

#### Flower 监控 Celery

访问: `http://your-domain.com:5555`
- 用户名: admin
- 密码: (来自 FLOWER_PASSWORD)

功能:
- 查看 Worker 状态
- 监控任务执行
- 查看任务历史
- 实时性能指标

#### 容器健康检查

```bash
# 查看容器健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' unlock-vip-api | jq

# 手动执行健康检查
docker exec unlock-vip-api curl -f http://localhost:8000/health
```

### 日志管理

#### 查看实时日志

```bash
# 所有服务
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f celery
docker-compose -f docker-compose.prod.yml logs -f nginx

# 最近 100 行
docker-compose -f docker-compose.prod.yml logs --tail=100 web
```

#### 日志文件位置

```bash
# 应用日志
/data/unlock-vip/logs/app/

# Celery 日志
/data/unlock-vip/logs/celery/

# Nginx 日志
/data/unlock-vip/logs/nginx/access.log
/data/unlock-vip/logs/nginx/error.log
```

#### 日志轮转

编辑 `/etc/logrotate.d/unlock-vip`:
```bash
/data/unlock-vip/logs/*/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker exec unlock-vip-nginx nginx -s reload > /dev/null 2>&1 || true
    endscript
}
```

### 性能监控

#### 容器资源使用

```bash
# 实时资源使用
docker stats

# 单个容器
docker stats unlock-vip-api

# 导出 CSV 格式
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
```

#### 系统资源监控

```bash
# CPU 和内存
top
htop

# 磁盘使用
df -h
du -sh /data/unlock-vip/*

# 网络连接
netstat -tunlp
ss -tunlp
```

### 数据库监控

#### MySQL 性能

```bash
# 进入 MySQL 容器
docker exec -it unlock-vip-mysql-prod mysql -uroot -p${DATABASE_ROOT_PASSWORD}

# 查看连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW PROCESSLIST;

# 查看慢查询
SHOW VARIABLES LIKE 'slow_query%';
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

# 查看表大小
SELECT 
    table_schema AS 'Database',
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'unlock_vip'
ORDER BY (data_length + index_length) DESC;
```

#### Redis 监控

```bash
# 进入 Redis 容器
docker exec -it unlock-vip-redis-prod redis-cli -a ${REDIS_PASSWORD}

# 查看信息
INFO
INFO stats
INFO memory

# 查看键数量
DBSIZE

# 查看慢查询
SLOWLOG GET 10

# 监控命令
MONITOR
```

### 备份策略

#### MySQL 自动备份

创建备份脚本 `/opt/scripts/backup-mysql.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/data/backups/mysql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/unlock-vip_$TIMESTAMP.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
docker exec unlock-vip-mysql-prod mysqldump \
  -uroot -p${DATABASE_ROOT_PASSWORD} \
  --single-transaction \
  --routines \
  --triggers \
  --databases unlock_vip > $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

添加定时任务:
```bash
chmod +x /opt/scripts/backup-mysql.sh

# 每天凌晨 2 点备份
crontab -e
0 2 * * * /opt/scripts/backup-mysql.sh >> /var/log/mysql-backup.log 2>&1
```

#### 恢复数据库

```bash
# 解压备份文件
gunzip backup.sql.gz

# 恢复数据库
docker exec -i unlock-vip-mysql-prod mysql -uroot -p${DATABASE_ROOT_PASSWORD} < backup.sql
```

---

## 🔧 故障排查

### 常见问题

#### 1. 容器无法启动

```bash
# 查看容器日志
docker logs unlock-vip-api

# 查看启动错误
docker-compose -f docker-compose.prod.yml logs --tail=50

# 检查配置文件
docker-compose -f docker-compose.prod.yml config
```

**可能原因:**
- 环境变量配置错误
- 端口被占用
- 磁盘空间不足
- 数据库连接失败

#### 2. 数据库连接失败

```bash
# 检查 MySQL 容器状态
docker ps | grep mysql

# 检查健康状态
docker inspect unlock-vip-mysql-prod | grep -A 10 Health

# 进入容器测试连接
docker exec -it unlock-vip-api bash
python -c "
from app.core.config import settings
from sqlalchemy import create_engine
engine = create_engine(settings.DATABASE_URL)
print(engine.connect())
"
```

**解决方案:**
- 检查 DATABASE_* 环境变量
- 确认 MySQL 容器已启动并健康
- 检查网络连接: `docker network inspect unlock-vip-network`

#### 3. Redis 连接失败

```bash
# 测试 Redis 连接
docker exec unlock-vip-redis-prod redis-cli -a ${REDIS_PASSWORD} ping

# 从 API 容器测试
docker exec unlock-vip-api python -c "
import redis
r = redis.Redis(host='redis', port=6379, password='${REDIS_PASSWORD}')
print(r.ping())
"
```

#### 4. Nginx 502 Bad Gateway

```bash
# 检查 Nginx 配置
docker exec unlock-vip-nginx nginx -t

# 查看 Nginx 错误日志
docker logs unlock-vip-nginx

# 检查后端服务
curl http://web:8000/health
```

**解决方案:**
- 确认 web 容器正在运行
- 检查 upstream 配置
- 增加超时时间

#### 5. Celery Worker 不工作

```bash
# 检查 Worker 状态
docker exec unlock-vip-celery celery -A app.core.celery_app inspect active

# 查看 Worker 日志
docker logs unlock-vip-celery --tail=100

# 检查 Redis 连接
docker exec unlock-vip-celery python -c "
from app.core.celery_app import app
print(app.control.inspect().active())
"
```

#### 6. 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 清理 Docker
docker system prune -a -f
docker volume prune -f

# 清理日志
find /data/unlock-vip/logs -name "*.log" -mtime +7 -delete

# 清理下载文件
find /data/unlock-vip/downloads -name "*.html" -mtime +7 -delete
```

### 性能优化

#### 数据库优化

```sql
-- 分析表
ANALYZE TABLE api_keys;
ANALYZE TABLE api_key_logs;

-- 优化表
OPTIMIZE TABLE api_keys;
OPTIMIZE TABLE api_key_logs;

-- 添加索引
CREATE INDEX idx_created_at ON api_key_logs(created_at);
CREATE INDEX idx_api_key_id ON api_key_logs(api_key_id);
```

#### Redis 优化

```bash
# 配置持久化策略
docker exec unlock-vip-redis-prod redis-cli -a ${REDIS_PASSWORD} CONFIG SET save "900 1 300 10 60 10000"

# 配置最大内存
docker exec unlock-vip-redis-prod redis-cli -a ${REDIS_PASSWORD} CONFIG SET maxmemory 256mb
docker exec unlock-vip-redis-prod redis-cli -a ${REDIS_PASSWORD} CONFIG SET maxmemory-policy allkeys-lru
```

#### Nginx 优化

在 `nginx/nginx.conf` 中:
```nginx
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # 启用缓存
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
    
    # 启用压缩
    gzip on;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript;
}
```

---

## 🔒 安全加固

### 系统安全

#### 1. 修改 SSH 端口

```bash
# 编辑 SSH 配置
vim /etc/ssh/sshd_config

# 修改端口
Port 22222

# 禁用 root 登录
PermitRootLogin no

# 重启 SSH
systemctl restart sshd
```

#### 2. 配置密钥登录

```bash
# 生成密钥对 (本地执行)
ssh-keygen -t rsa -b 4096

# 上传公钥
ssh-copy-id -p 22222 your-user@your-server-ip

# 禁用密码登录
vim /etc/ssh/sshd_config
PasswordAuthentication no
```

#### 3. 安装 fail2ban

```bash
# 安装
yum install -y fail2ban

# 配置
cat > /etc/fail2ban/jail.local <<EOF
[sshd]
enabled = true
port = 22222
logpath = /var/log/secure
maxretry = 3
bantime = 3600
EOF

# 启动
systemctl enable fail2ban
systemctl start fail2ban
```

### 应用安全

#### 1. 使用强密码

所有密码必须满足:
- 至少 16 位
- 包含大小写字母、数字、特殊字符
- 定期更换

#### 2. 限制网络访问

```bash
# 仅允许特定 IP 访问管理接口
# 在 nginx/conf.d/unlock-vip.conf 中添加:
location /api/admin/ {
    allow 1.2.3.4;  # 你的 IP
    deny all;
    proxy_pass http://unlock_vip_backend;
}
```

#### 3. 启用 HTTPS

强制所有连接使用 HTTPS:
```nginx
# 自动跳转
server {
    listen 80;
    return 301 https://$server_name$request_uri;
}
```

#### 4. 定期更新

```bash
# 系统更新
yum update -y

# Docker 更新
yum update docker-ce -y

# 应用更新
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 数据安全

#### 1. 加密敏感配置

```bash
# 使用 Docker secrets (Swarm 模式)
echo "your_password" | docker secret create db_password -
```

#### 2. 备份加密

```bash
# 加密备份文件
gpg --symmetric --cipher-algo AES256 backup.sql

# 解密
gpg --decrypt backup.sql.gpg > backup.sql
```

#### 3. 审计日志

记录所有管理操作:
```python
# 在 app/api/admin.py 中
@router.post("/keys")
async def create_key(...):
    # 记录操作
    logger.info(f"Admin created API key: {name} from IP: {request.client.host}")
```

---

## 📖 附录

### 快速命令参考

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 进入容器
docker exec -it unlock-vip-api bash

# 数据库备份
docker exec unlock-vip-mysql-prod mysqldump -uroot -p${DATABASE_ROOT_PASSWORD} unlock_vip > backup.sql

# 更新镜像
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 清理资源
docker system prune -a -f
```

### 环境变量速查

| 变量名 | 说明 | 示例 |
|--------|------|------|
| DOCKER_REGISTRY | 镜像仓库地址 | registry.cn-hangzhou.aliyuncs.com/your-namespace |
| VERSION | 镜像版本 | 1.0.0 |
| DATABASE_PASSWORD | 数据库密码 | 强密码 |
| REDIS_PASSWORD | Redis密码 | 强密码 |
| CSDN_USERNAME | CSDN用户名 | your_username |
| CSDN_PASSWORD | CSDN密码 | your_password |
| ADMIN_MASTER_KEY | 管理员密钥 | 生成的密钥 |
| CAPTCHA_SERVICE | 验证码服务 | mock/chaojiying |

### 相关文档

- [API 快速参考](API_QUICK_REFERENCE.md)
- [Admin 安全配置](ADMIN_SECURITY.md)
- [文件清理系统](FILE_CLEANUP.md)
- [Celery Beat 指南](CELERY_BEAT_GUIDE.md)

---

## 💬 技术支持

遇到问题？

1. 查看本文档的 [故障排查](#故障排查) 部分
2. 查看容器日志: `docker-compose logs`
3. 查看 GitHub Issues
4. 联系技术支持

---

**部署成功后，别忘了:**
- ✅ 修改所有默认密码
- ✅ 配置 SSL 证书
- ✅ 设置定期备份
- ✅ 配置监控告警
- ✅ 进行压力测试

祝部署顺利！🎉
