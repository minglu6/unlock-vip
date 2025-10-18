# Docker 部署指南

使用 Docker 和 Docker Compose 部署 Unlock-VIP 服务。

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 服务器至少 1GB RAM

## 快速开始（服务器部署）

### 第一步：安装 Docker

如果服务器还没有安装 Docker，执行以下命令：

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | bash

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 第二步：准备项目文件

在服务器上（假设已克隆到 `/opt/unlock-vip`）：

```bash
cd /opt/unlock-vip

# 确认文件结构
ls -la
# 应该看到: Dockerfile, docker-compose.yml, app/, requirements.txt 等
```

### 第三步：配置 cookies

**重要**: 必须创建 `cookies.json` 文件

```bash
# 创建 cookies.json
nano cookies.json
```

粘贴以下格式的内容（替换为你的实际 cookies）：

```json
{
    "UserName": "your_username",
    "UserToken": "your_token_here",
    "uuid_tt_dd": "your_uuid_here",
    "c_login_app": "your_login_app_token"
}
```

**获取 cookies 方法**：
1. 登录 CSDN 网站（https://blog.csdn.net）
2. 打开浏览器开发者工具（F12）
3. 切换到 "Application" 或 "存储" 标签
4. 点击 "Cookies" → "https://blog.csdn.net"
5. 找到并复制以下 cookie 的值：
   - `UserName`
   - `UserToken`
   - `uuid_tt_dd`
   - `c_login_app`

保存文件：`Ctrl+X` → `Y` → `Enter`

### 第四步：构建并启动服务

```bash
# 构建 Docker 镜像
docker compose build

# 启动服务（后台运行）
docker compose up -d

# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 第五步：验证部署

```bash
# 方法1: 使用 curl
curl http://localhost:8001/health
# 应该返回: {"status":"ok"}

# 方法2: 在浏览器访问
# http://175.24.164.85:8001/docs
# http://175.24.164.85:8001/health
```

### 第六步：配置防火墙（重要）

```bash
# 如果使用 ufw
sudo ufw allow 8001/tcp
sudo ufw reload

# 如果是云服务器（阿里云/腾讯云/AWS）
# 在控制台的安全组中开放 8001 端口
```

## 配置 Nginx 反向代理（推荐）

为了更好的性能和安全性，建议使用 Nginx 作为反向代理。

### 安装 Nginx

```bash
sudo apt update
sudo apt install -y nginx
```

### 配置 Nginx

```bash
# 创建配置文件
sudo nano /etc/nginx/sites-available/unlock-vip
```

粘贴以下内容：

```nginx
server {
    listen 80;
    server_name 175.24.164.85;  # 改成你的域名或保持IP

    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
```

启用配置：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/unlock-vip /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重新加载
sudo systemctl reload nginx

# 开放 80 端口
sudo ufw allow 80/tcp
```

现在可以通过 `http://175.24.164.85/docs` 访问了！

## Docker 常用命令

### 容器管理

```bash
# 查看运行状态
docker compose ps

# 启动服务
docker compose start

# 停止服务
docker compose stop

# 重启服务
docker compose restart

# 停止并删除容器
docker compose down

# 停止并删除容器+镜像
docker compose down --rmi all
```

### 日志查看

```bash
# 查看实时日志
docker compose logs -f

# 查看最近100行日志
docker compose logs --tail=100

# 查看特定服务日志
docker compose logs -f unlock-vip
```

### 进入容器

```bash
# 进入容器 shell
docker compose exec unlock-vip bash

# 或使用 sh（如果 bash 不可用）
docker compose exec unlock-vip sh

# 在容器中执行命令
docker compose exec unlock-vip ls -la
```

### 更新代码

```bash
cd /opt/unlock-vip

# 拉取最新代码
git pull

# 重新构建并启动
docker compose build
docker compose up -d

# 或者一条命令
docker compose up -d --build
```

### 清理资源

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理所有未使用资源
docker system prune -a
```

## 环境变量配置

可以在 `docker-compose.yml` 中修改环境变量：

```yaml
environment:
  - PORT=8001
  - THREAD_POOL_WORKERS=4  # 根据服务器配置调整
```

或者创建 `.env` 文件：

```bash
nano .env
```

```env
PORT=8001
THREAD_POOL_WORKERS=4
```

然后在 `docker-compose.yml` 中引用：

```yaml
services:
  unlock-vip:
    env_file:
      - .env
```

## 性能优化

### 1. 调整 Worker 数量

根据服务器 CPU 核心数调整：

```yaml
environment:
  - THREAD_POOL_WORKERS=4  # 2 * CPU核心数
```

### 2. 限制容器资源

```yaml
services:
  unlock-vip:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 3. 使用多进程

修改 Dockerfile 中的启动命令：

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

## 监控与健康检查

### 查看健康状态

```bash
# 查看容器健康状态
docker compose ps

# 查看详细健康检查信息
docker inspect unlock-vip | grep -A 10 Health
```

### 自动重启

`docker-compose.yml` 中已配置 `restart: unless-stopped`，容器会在异常退出时自动重启。

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker compose logs

# 查看容器状态
docker compose ps -a

# 检查镜像构建
docker compose build --no-cache
```

### 端口被占用

```bash
# 检查端口占用
netstat -tlnp | grep 8001

# 或使用 ss
ss -tlnp | grep 8001

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8002:8001"  # 改用 8002 端口
```

### cookies.json 未找到

```bash
# 确认文件存在
ls -la cookies.json

# 检查文件内容
cat cookies.json

# 确保 docker-compose.yml 中正确挂载
volumes:
  - ./cookies.json:/app/cookies.json:ro
```

### 容器内存不足

```bash
# 查看容器资源使用
docker stats unlock-vip

# 增加内存限制
docker compose down
# 修改 docker-compose.yml 增加内存限制
docker compose up -d
```

## 备份与恢复

### 备份

```bash
# 备份 cookies.json
cp cookies.json cookies.json.backup

# 备份下载的文件
tar -czf downloads-backup.tar.gz downloads/

# 导出 Docker 镜像
docker save unlock-vip:latest | gzip > unlock-vip-image.tar.gz
```

### 恢复

```bash
# 恢复 cookies
cp cookies.json.backup cookies.json

# 恢复下载文件
tar -xzf downloads-backup.tar.gz

# 导入 Docker 镜像
docker load < unlock-vip-image.tar.gz
```

## 生产环境建议

1. **使用 Nginx 反向代理**: 不要直接暴露应用端口
2. **配置 HTTPS**: 使用 Let's Encrypt 免费证书
3. **定期更新**: 保持代码和依赖包最新
4. **监控日志**: 定期检查应用日志
5. **备份 cookies**: cookies 失效后需要重新获取
6. **限制访问**: 使用防火墙或 Nginx 限制访问来源

## 测试 API

### 下载文章

```bash
curl -X POST "http://175.24.164.85:8001/api/article/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://blog.csdn.net/username/article/details/123456"}'
```

### 获取文件下载链接

```bash
curl -X POST "http://175.24.164.85:8001/api/file/get-download-link" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://download.csdn.net/download/user/12345"}'
```

## 完整部署示例（从零开始）

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash
sudo systemctl start docker

# 2. 克隆项目
cd /opt
git clone https://github.com/your-username/unlock-vip.git
cd unlock-vip

# 3. 配置 cookies
nano cookies.json
# 粘贴 cookies 内容并保存

# 4. 启动服务
docker compose up -d

# 5. 查看日志
docker compose logs -f

# 6. 测试访问
curl http://localhost:8001/health

# 7. 配置防火墙
sudo ufw allow 8001/tcp
```

## 联系支持

如有问题，请检查：
1. Docker 和 Docker Compose 版本
2. cookies.json 文件格式和内容
3. 容器日志: `docker compose logs`
4. 防火墙和安全组配置
