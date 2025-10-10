# 🚀 快速部署步骤（阿里云 Ubuntu 24.04）

## ✅ 前提条件（您已完成）
- ✅ 代码已拉取到服务器
- ✅ Docker 和 Docker Compose 已安装
- ✅ `.env.prod` 配置文件已创建并修改

---

## 📋 部署步骤

### 方式1️⃣：一键自动部署（推荐）⭐

```bash
# 进入项目目录
cd /opt/unlock-vip  # 或您的项目路径

# 运行一键部署脚本
bash deploy-production.sh
```

**脚本会自动完成**：
- ✅ 检查系统环境
- ✅ 配置防火墙
- ✅ 拉取 Docker 镜像（MySQL, Redis）
- ✅ 构建应用镜像
- ✅ 启动所有容器
- ✅ 初始化数据库
- ✅ 检查服务状态
- ✅ 可选：配置 Nginx 反向代理
- ✅ 可选：配置 SSL 证书
- ✅ 可选：配置自动备份

---

### 方式2️⃣：手动部署（分步执行）

#### **第1步：检查配置**

```bash
# 确认文件存在
ls -la .env.prod cookies.json docker-compose.prod.yml

# 运行部署前检查（可选但推荐）
bash pre-deploy-check.sh
```

#### **第2步：拉取并启动服务**

```bash
# 拉取镜像并启动容器（会自动拉取 MySQL 和 Redis）
docker-compose -f docker-compose.prod.yml up -d

# 查看启动日志
docker-compose -f docker-compose.prod.yml logs -f
```

#### **第3步：等待服务启动**

```bash
# 等待 30 秒让 MySQL 完成初始化
sleep 30

# 检查容器状态（应该都是 Up 和 healthy）
docker-compose -f docker-compose.prod.yml ps
```

#### **第4步：初始化数据库**

```bash
# 初始化数据库表
docker-compose -f docker-compose.prod.yml exec web python manage_db.py init

# 创建第一个 API Key
docker-compose -f docker-compose.prod.yml exec web python manage_db.py create "测试密钥"
```

#### **第5步：配置防火墙**

```bash
# 允许 HTTP 和 HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # API 端口

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

#### **第6步：测试 API**

```bash
# 获取您的 API Key
docker-compose -f docker-compose.prod.yml exec web python manage_db.py list

# 测试健康检查
curl http://localhost:8000/health

# 测试文件服务（替换 YOUR_API_KEY）
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/api/file/health
```

---

## 🎯 验证部署成功

### **1. 检查容器状态**

```bash
docker-compose -f docker-compose.prod.yml ps
```

**预期输出**：
```
NAME                        STATUS                  PORTS
unlock-vip-mysql-prod      Up (healthy)           3306/tcp
unlock-vip-redis-prod      Up (healthy)           6379/tcp
unlock-vip-api-prod        Up (healthy)           0.0.0.0:8000->8000/tcp
unlock-vip-celery-prod     Up                     
unlock-vip-celery-beat     Up                     
unlock-vip-flower-prod     Up                     0.0.0.0:5555->5555/tcp
```

### **2. 查看日志**

```bash
# 查看应用日志
docker-compose -f docker-compose.prod.yml logs -f web

# 查看 Celery 日志
docker-compose -f docker-compose.prod.yml logs -f celery

# 查看所有日志
docker-compose -f docker-compose.prod.yml logs -f
```

### **3. 测试 API 端点**

```bash
# 在服务器上测试
curl http://localhost:8000/health

# 从外部测试（替换为您的服务器 IP）
curl http://服务器IP:8000/health
```

**预期响应**：
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 🛠️ 常用命令

### **服务管理**

```bash
# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 重启单个服务
docker-compose -f docker-compose.prod.yml restart web
```

### **日志查看**

```bash
# 实时日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看最近 100 行
docker-compose -f docker-compose.prod.yml logs --tail=100

# 查看特定服务
docker-compose -f docker-compose.prod.yml logs -f web
```

### **API Key 管理**

```bash
# 列出所有 API Key
docker-compose -f docker-compose.prod.yml exec web python manage_db.py list

# 创建新 Key
docker-compose -f docker-compose.prod.yml exec web python manage_db.py create "密钥名称"

# 删除 Key
docker-compose -f docker-compose.prod.yml exec web python manage_db.py delete <key_id>
```

### **数据库操作**

```bash
# 进入 MySQL
docker exec -it unlock-vip-mysql-prod mysql -u unlock_vip_user -p

# 备份数据库
docker exec unlock-vip-mysql-prod mysqldump -u unlock_vip_user -p unlock_vip > backup.sql

# 恢复数据库
docker exec -i unlock-vip-mysql-prod mysql -u unlock_vip_user -p unlock_vip < backup.sql
```

---

## 🔧 配置 Nginx 反向代理（可选）

### **安装 Nginx**

```bash
sudo apt update
sudo apt install -y nginx
```

### **配置反向代理**

```bash
# 创建配置文件
sudo nano /etc/nginx/sites-available/unlock-vip
```

**配置内容**：
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**启用配置**：
```bash
sudo ln -s /etc/nginx/sites-available/unlock-vip /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 配置 SSL（可选）

```bash
# 使用 Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# 自动配置 SSL
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## ❗ 常见问题

### **问题1：容器启动失败**

```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs

# 检查端口占用
sudo netstat -tlnp | grep -E '3306|6379|8000'
```

### **问题2：数据库连接失败**

```bash
# 检查 MySQL 是否健康
docker-compose -f docker-compose.prod.yml ps mysql

# 重启 MySQL
docker-compose -f docker-compose.prod.yml restart mysql

# 等待 30 秒后重启应用
docker-compose -f docker-compose.prod.yml restart web
```

### **问题3：API 无法访问**

```bash
# 检查防火墙
sudo ufw status

# 检查容器端口映射
docker-compose -f docker-compose.prod.yml ps

# 检查应用日志
docker-compose -f docker-compose.prod.yml logs web
```

### **问题4：cookies.json 未找到**

```bash
# 确认文件存在
ls -la cookies.json

# 重新上传
# 在本地执行: scp cookies.json root@服务器IP:/opt/unlock-vip/
```

---

## 📊 监控面板

### **Flower（Celery 监控）**

访问：`http://服务器IP:5555`

用户名/密码：在 `.env.prod` 中配置的 `FLOWER_USER` 和 `FLOWER_PASSWORD`

### **API 文档**

访问：`http://服务器IP:8000/docs`

---

## 🎉 部署完成！

访问您的 API：
- **健康检查**：`http://服务器IP:8000/health`
- **API 文档**：`http://服务器IP:8000/docs`
- **Flower 监控**：`http://服务器IP:5555`

---

## 📚 相关文档

- [完整部署指南](docs/ALIYUN_PRODUCTION_DEPLOY.md)
- [部署文件清单](DEPLOYMENT_GUIDE.md)
- [快速部署指南](PRODUCTION_DEPLOY_README.md)
- [部署前检查说明](pre-deploy-check.sh)

---

**祝您部署顺利！** 🚀

如有问题，请查看日志：`docker-compose -f docker-compose.prod.yml logs -f`
