# 云服务器部署指南

## 系统要求

- Ubuntu 20.04+ / Debian 11+ (或其他 Linux 发行版)
- Python 3.8+
- 至少 1GB RAM
- 至少 10GB 磁盘空间

## 快速部署（推荐）

### 第一步：准备服务器

```bash
# 连接到服务器
ssh root@your_server_ip

# 安装必要软件
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx supervisor
```

### 第二步：下载代码

```bash
# 克隆代码到 /opt 目录
cd /opt
git clone https://github.com/your-username/unlock-vip.git
cd unlock-vip

# 或者使用 scp 从本地上传
# 本地执行: scp -r /path/to/unlock-vip root@your_server_ip:/opt/
```

### 第三步：配置 cookies

```bash
cd /opt/unlock-vip

# 方法1: 从本地上传 cookies.json
# 本地执行: scp cookies.json root@your_server_ip:/opt/unlock-vip/

# 方法2: 在服务器上创建
nano cookies.json
# 粘贴你的 CSDN cookies
```

### 第四步：运行部署脚本

```bash
cd /opt/unlock-vip
chmod +x deploy/deploy.sh
bash deploy/deploy.sh
```

### 第五步：配置域名（可选）

如果你有域名，需要修改 Nginx 配置：

```bash
nano /etc/nginx/sites-available/unlock-vip
# 将 server_name 改为你的域名
# 例如: server_name api.yourdomain.com;

# 重新加载 nginx
nginx -t
systemctl reload nginx
```

### 第六步：配置 HTTPS（推荐）

```bash
# 安装 certbot
apt install -y certbot python3-certbot-nginx

# 申请 SSL 证书（自动配置 nginx）
certbot --nginx -d your_domain.com

# 自动续期
certbot renew --dry-run
```

## 手动部署（详细步骤）

### 1. 安装依赖

```bash
cd /opt/unlock-vip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置 Supervisor

```bash
# 复制配置文件
cp deploy/supervisor.conf /etc/supervisor/conf.d/unlock-vip.conf

# 创建日志目录
mkdir -p /var/log/unlock-vip

# 重新加载配置
supervisorctl reread
supervisorctl update
supervisorctl start unlock-vip
```

### 3. 配置 Nginx

```bash
# 复制配置文件
cp deploy/nginx.conf /etc/nginx/sites-available/unlock-vip

# 修改域名（如果需要）
nano /etc/nginx/sites-available/unlock-vip

# 创建软链接
ln -s /etc/nginx/sites-available/unlock-vip /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重新加载
systemctl reload nginx
```

### 4. 配置防火墙

```bash
# 如果使用 ufw
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload

# 如果使用阿里云/腾讯云
# 在控制台安全组中开放 80 和 443 端口
```

## 常用运维命令

### Supervisor 进程管理

```bash
# 查看状态
supervisorctl status unlock-vip

# 启动服务
supervisorctl start unlock-vip

# 停止服务
supervisorctl stop unlock-vip

# 重启服务
supervisorctl restart unlock-vip

# 查看日志
tail -f /var/log/unlock-vip/app.log
```

### Nginx 管理

```bash
# 测试配置
nginx -t

# 重新加载
systemctl reload nginx

# 重启
systemctl restart nginx

# 查看状态
systemctl status nginx

# 查看日志
tail -f /var/log/nginx/unlock-vip-access.log
tail -f /var/log/nginx/unlock-vip-error.log
```

### 更新代码

```bash
cd /opt/unlock-vip

# 拉取最新代码
git pull

# 或者从本地上传
# scp -r /path/to/unlock-vip/* root@your_server_ip:/opt/unlock-vip/

# 重启服务
supervisorctl restart unlock-vip
```

### 查看日志

```bash
# 应用日志
tail -f /var/log/unlock-vip/app.log

# Nginx 访问日志
tail -f /var/log/nginx/unlock-vip-access.log

# Nginx 错误日志
tail -f /var/log/nginx/unlock-vip-error.log

# Supervisor 日志
tail -f /var/log/supervisor/supervisord.log
```

## 测试部署

### 1. 健康检查

```bash
curl http://your_server_ip/health
# 预期输出: {"status":"ok"}
```

### 2. API 文档

浏览器访问: `http://your_server_ip/docs`

### 3. 测试下载

```bash
curl -X POST "http://your_server_ip/api/article/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://blog.csdn.net/username/article/details/123456"}'
```

## 性能优化

### 1. 增加 Worker 数量

编辑 `/etc/supervisor/conf.d/unlock-vip.conf`:

```ini
command=/opt/unlock-vip/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 4
```

### 2. Nginx 缓存配置

编辑 `/etc/nginx/sites-available/unlock-vip`:

```nginx
# 在 http 块中添加
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;

# 在 location 块中添加
proxy_cache my_cache;
proxy_cache_valid 200 1h;
```

### 3. 限流配置

编辑 `/etc/nginx/sites-available/unlock-vip`:

```nginx
# 在 http 块中添加
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# 在 location 块中添加
limit_req zone=api_limit burst=20 nodelay;
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
tail -100 /var/log/unlock-vip/app.log

# 检查端口占用
netstat -tlnp | grep 8001

# 手动测试启动
cd /opt/unlock-vip
source .venv/bin/activate
python run.py
```

### Nginx 502 错误

```bash
# 检查应用是否运行
supervisorctl status unlock-vip

# 检查端口监听
netstat -tlnp | grep 8001

# 查看 nginx 错误日志
tail -f /var/log/nginx/unlock-vip-error.log
```

### Cookies 失效

```bash
# 更新 cookies.json
nano /opt/unlock-vip/cookies.json

# 重启服务
supervisorctl restart unlock-vip
```

## 安全建议

1. **限制 IP 访问**: 在 Nginx 中配置白名单
2. **添加 API Key**: 修改代码添加认证中间件
3. **HTTPS**: 使用 Let's Encrypt 免费证书
4. **定期更新**: 保持系统和依赖包更新
5. **备份**: 定期备份 cookies.json 和配置文件

## 监控告警（可选）

### 使用 Prometheus + Grafana

```bash
# 安装 Prometheus
apt install -y prometheus

# 配置监控端点
# 在应用中添加 prometheus_client
pip install prometheus-client
```

### 简单邮件告警

```bash
# 创建监控脚本
cat > /opt/check_service.sh << 'EOF'
#!/bin/bash
if ! supervisorctl status unlock-vip | grep -q RUNNING; then
    echo "unlock-vip service is down!" | mail -s "Service Alert" your@email.com
fi
EOF

chmod +x /opt/check_service.sh

# 添加到 crontab (每5分钟检查一次)
crontab -e
# 添加: */5 * * * * /opt/check_service.sh
```

## 联系与支持

如有问题，请查看项目文档或提交 Issue。
