# 🚀 阿里云部署完整指南

## 📋 部署前准备清单

### 1. 服务器要求
- [x] **操作系统**: Ubuntu 20.04+ / CentOS 7+
- [x] **内存**: 最低2GB，推荐4GB
- [x] **CPU**: 2核心以上
- [x] **磁盘**: 20GB以上可用空间
- [x] **Python版本**: 3.9+

### 2. 必需软件
- [x] Docker & Docker Compose
- [x] Git
- [x] Nginx（可选，用于反向代理）
- [x] Redis（用于Celery）
- [x] MySQL 8.0+

### 3. 必需文件
- [x] `cookies.json` - CSDN登录状态
- [x] `.env.prod` - 生产环境配置
- [x] SSL证书（如需HTTPS）

---

## 🛠️ 快速部署（推荐）

### 方式一：Docker Compose一键部署

#### 1. 连接服务器

```bash
ssh root@your-server-ip
```

#### 2. 安装Docker

```bash
# 安装Docker
curl -fsSL https://get.docker.com | bash

# 启动Docker
systemctl start docker
systemctl enable docker

# 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### 3. 克隆项目

```bash
cd /opt
git clone https://github.com/your-username/unlock-vip.git
cd unlock-vip
```

#### 4. 配置环境变量

```bash
# 复制生产环境配置
cp .env.prod.example .env.prod

# 编辑配置文件
nano .env.prod
```

**必须修改的配置**：

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=your_strong_password_here
MYSQL_DATABASE=unlock_vip
MYSQL_USER=unlock_user
MYSQL_PASSWORD=your_user_password_here

# Redis配置
REDIS_PASSWORD=your_redis_password_here

# 应用配置
SECRET_KEY=your_secret_key_here_generate_with_openssl
ADMIN_KEY=your_admin_key_here

# 域名配置（如有）
DOMAIN=your-domain.com
```

#### 5. 上传cookies.json

```bash
# 从本地上传（在本地执行）
scp cookies.json root@your-server-ip:/opt/unlock-vip/

# 或在服务器上创建
nano /opt/unlock-vip/cookies.json
# 粘贴内容并保存
```

#### 6. 启动服务

```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d

# 查看启动日志
docker-compose -f docker-compose.prod.yml logs -f
```

#### 7. 验证部署

```bash
# 检查容器状态
docker-compose -f docker-compose.prod.yml ps

# 测试API
curl http://localhost:8000/health
```

---

## 🔧 手动部署（传统方式）

### 1. 安装系统依赖

```bash
# Ubuntu/Debian
apt update
apt install -y python3 python3-pip python3-venv nginx redis-server mysql-server

# CentOS/RHEL
yum update
yum install -y python3 python3-pip nginx redis mysql-server
```

### 2. 创建部署目录

```bash
mkdir -p /opt/unlock-vip
cd /opt/unlock-vip
```

### 3. 克隆项目

```bash
git clone https://github.com/your-username/unlock-vip.git .
```

### 4. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 配置数据库

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE unlock_vip CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'unlock_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON unlock_vip.* TO 'unlock_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 6. 配置环境变量

```bash
cp .env.example .env
nano .env
```

修改配置：

```bash
DATABASE_URL=mysql+pymysql://unlock_user:your_password@localhost:3306/unlock_vip
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=$(openssl rand -hex 32)
```

### 7. 初始化数据库

```bash
python manage_db.py --init
```

### 8. 配置systemd服务

创建 `/etc/systemd/system/unlock-vip.service`:

```ini
[Unit]
Description=Unlock-VIP FastAPI Application
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/unlock-vip
Environment="PATH=/opt/unlock-vip/venv/bin"
ExecStart=/opt/unlock-vip/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

创建 `/etc/systemd/system/unlock-vip-celery.service`:

```ini
[Unit]
Description=Unlock-VIP Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/unlock-vip
Environment="PATH=/opt/unlock-vip/venv/bin"
ExecStart=/opt/unlock-vip/venv/bin/celery -A celery_worker.celery_app worker -l info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 9. 启动服务

```bash
# 重载systemd
systemctl daemon-reload

# 启动服务
systemctl start unlock-vip
systemctl start unlock-vip-celery

# 设置开机自启
systemctl enable unlock-vip
systemctl enable unlock-vip-celery

# 查看状态
systemctl status unlock-vip
systemctl status unlock-vip-celery
```

### 10. 配置Nginx反向代理

创建 `/etc/nginx/sites-available/unlock-vip`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件（如需要）
    location /downloads/ {
        alias /opt/unlock-vip/downloads/;
        autoindex off;
    }
}
```

启用配置：

```bash
ln -s /etc/nginx/sites-available/unlock-vip /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## 🔒 安全配置

### 1. 配置防火墙

```bash
# UFW (Ubuntu)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Firewalld (CentOS)
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

### 2. 配置SSL证书（Let's Encrypt）

```bash
# 安装Certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

### 3. 修改默认密码

```bash
# 生成管理员密钥
cd /opt/unlock-vip
source venv/bin/activate
python scripts/generate_admin_key.py
```

### 4. 限制访问

在Nginx配置中添加IP白名单：

```nginx
location /api/admin/ {
    allow 123.45.67.89;  # 你的IP
    deny all;
    
    proxy_pass http://127.0.0.1:8000;
    # ... 其他配置
}
```

---

## 📊 监控和维护

### 1. 查看日志

```bash
# Docker方式
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f celery

# Systemd方式
journalctl -u unlock-vip -f
journalctl -u unlock-vip-celery -f
```

### 2. 重启服务

```bash
# Docker方式
docker-compose -f docker-compose.prod.yml restart

# Systemd方式
systemctl restart unlock-vip
systemctl restart unlock-vip-celery
```

### 3. 备份数据库

```bash
# 创建备份脚本
cat > /opt/backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec unlock-vip-mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} unlock_vip > $BACKUP_DIR/db_$DATE.sql

# 保留最近7天的备份
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql"
EOF

chmod +x /opt/backup_db.sh

# 添加到crontab（每天凌晨2点备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup_db.sh") | crontab -
```

### 4. 更新部署

```bash
# Docker方式
cd /opt/unlock-vip
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 手动方式
cd /opt/unlock-vip
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart unlock-vip
systemctl restart unlock-vip-celery
```

---

## 🐛 常见问题排查

### 1. 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep 8000
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### 2. 数据库连接失败

```bash
# 检查MySQL状态
systemctl status mysql
docker logs unlock-vip-mysql

# 测试连接
mysql -h 127.0.0.1 -u unlock_user -p unlock_vip
```

### 3. Redis连接失败

```bash
# 检查Redis状态
systemctl status redis
docker logs unlock-vip-redis

# 测试连接
redis-cli ping
```

### 4. 权限问题

```bash
# 修复文件权限
chown -R www-data:www-data /opt/unlock-vip
chmod -R 755 /opt/unlock-vip
```

### 5. Celery任务不执行

```bash
# 清空Redis队列
redis-cli FLUSHALL

# 重启Celery
systemctl restart unlock-vip-celery
```

---

## 📈 性能优化

### 1. Nginx缓存配置

```nginx
http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
    
    server {
        location /api/ {
            proxy_cache api_cache;
            proxy_cache_valid 200 5m;
            proxy_cache_key "$scheme$request_method$host$request_uri";
            add_header X-Cache-Status $upstream_cache_status;
            
            proxy_pass http://127.0.0.1:8000;
        }
    }
}
```

### 2. 增加Gunicorn工作进程

修改 `run.py` 或创建 `gunicorn_config.py`:

```python
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5
timeout = 120
```

### 3. 调整线程池

修改 `app/services/file_service.py`:

```python
self._executor = ThreadPoolExecutor(
    max_workers=8,  # 根据CPU核心数调整
    thread_name_prefix="FileDownload"
)
```

---

## ✅ 部署检查清单

部署完成后，逐项检查：

- [ ] 服务器可以访问
- [ ] Docker容器全部运行
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] API健康检查通过 (`/health`)
- [ ] 文件下载API正常 (`/api/file/health`)
- [ ] Celery任务执行正常
- [ ] Nginx反向代理工作
- [ ] SSL证书配置正确（如有）
- [ ] 防火墙规则生效
- [ ] 日志正常输出
- [ ] 备份脚本测试通过

---

## 📞 技术支持

遇到问题？

1. 查看日志文件
2. 参考 [常见问题](#常见问题排查)
3. 查看项目文档：`docs/README.md`
4. 提交Issue到GitHub仓库

---

**最后更新**: 2025-10-03  
**适用版本**: v2.0.0+
