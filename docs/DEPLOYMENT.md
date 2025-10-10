# 生产环境部署指南

## 📦 项目结构

```
unlock-vip/
├── app/                    # 应用主目录
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   └── tasks/             # Celery 任务
├── docs/                  # 文档
├── downloads/             # 文章下载目录
├── tests/                 # 测试文件
├── .env                   # 环境变量配置（不提交到 Git）
├── .env.example           # 环境变量示例
├── .gitignore             # Git 忽略文件
├── requirements.txt       # Python 依赖
└── run.py                 # 启动脚本
```

## 🚀 部署步骤

### 1. 环境准备

#### 系统要求
- Python 3.8+
- Redis 5.0+
- 至少 1GB 内存
- 网络连接稳定

#### 安装依赖
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```env
# CSDN 账号（必需）
CSDN_USERNAME=your_username
CSDN_PASSWORD=your_password

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 服务器端口
PORT=8000

# 验证码服务（可选）
CAPTCHA_SERVICE=mock
```

### 3. 启动服务

#### 方式 1: 手动启动（开发/测试）

**终端 1 - Redis:**
```bash
docker run -d --name unlock-vip-redis -p 6379:6379 redis:latest
```

**终端 2 - Celery Worker:**
```bash
# Windows
celery -A app.core.celery_app worker --loglevel=info -P solo --pool=solo

# Linux/Mac
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

**终端 3 - FastAPI Server:**
```bash
python run.py
```

#### 方式 2: 使用进程管理器（生产环境推荐）

**使用 Supervisor (Linux)**

创建 `/etc/supervisor/conf.d/unlock-vip.conf`:

```ini
[program:unlock-vip-api]
command=/path/to/venv/bin/python run.py
directory=/path/to/unlock-vip
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/unlock-vip/api.err.log
stdout_logfile=/var/log/unlock-vip/api.out.log

[program:unlock-vip-celery]
command=/path/to/venv/bin/celery -A app.core.celery_app worker --loglevel=info --concurrency=4
directory=/path/to/unlock-vip
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/unlock-vip/celery.err.log
stdout_logfile=/var/log/unlock-vip/celery.out.log
```

启动服务：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start unlock-vip-api unlock-vip-celery
```

**使用 PM2 (Windows/Linux)**

```bash
# 安装 PM2
npm install -g pm2

# 启动服务
pm2 start run.py --name unlock-vip-api --interpreter python
pm2 start "celery -A app.core.celery_app worker --loglevel=info -P solo" --name unlock-vip-celery

# 保存配置
pm2 save
pm2 startup
```

#### 方式 3: Docker Compose（推荐）

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    env_file:
      - .env
    depends_on:
      - redis
    restart: always
    command: python run.py

  celery:
    build: .
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    env_file:
      - .env
    depends_on:
      - redis
    restart: always
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4

volumes:
  redis_data:
```

启动：
```bash
docker-compose up -d
```

### 4. 反向代理配置（生产环境）

#### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

### 5. 健康检查

访问以下端点验证服务状态：

- **健康检查**: `GET http://localhost:8000/health`
- **API 文档**: `GET http://localhost:8000/docs`

### 6. 监控（可选）

#### Flower - Celery 监控

```bash
pip install flower
celery -A app.core.celery_app flower --port=5555
```

访问: http://localhost:5555

## 🔧 生产环境优化

### 1. 性能优化

**Celery Worker 并发数:**
```bash
# 根据 CPU 核心数调整
celery -A app.core.celery_app worker --concurrency=4
```

**多个 Worker:**
```bash
# 启动多个 Worker 实例
celery -A app.core.celery_app worker -n worker1@%h
celery -A app.core.celery_app worker -n worker2@%h
```

### 2. 日志配置

修改 `run.py` 添加日志配置：

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 3. 安全配置

- ✅ 使用环境变量管理敏感信息
- ✅ 不要将 `.env` 提交到版本控制
- ✅ Redis 设置密码保护
- ✅ 使用 HTTPS (生产环境)
- ✅ 限制 API 访问频率

### 4. 备份策略

- 定期备份 `cookies.json`
- 备份下载的文章文件
- 备份 Redis 数据（如需要）

## 📊 监控指标

### 关键指标
- API 响应时间
- Celery 任务成功率
- Redis 连接状态
- 磁盘空间使用
- 内存使用情况

### 告警设置
- Worker 离线告警
- Redis 连接失败告警
- 磁盘空间不足告警

## 🐛 故障排查

### 常见问题

**1. Worker 无法启动**
- 检查 Redis 连接
- 查看 Worker 日志
- 确认虚拟环境已激活

**2. 任务一直 PENDING**
- 检查 Worker 是否运行
- 验证队列配置
- 查看 Celery 日志

**3. 下载失败**
- 检查 CSDN 账号是否有效
- 验证网络连接
- 查看 cookies.json 是否存在

## 📞 技术支持

如遇问题，请检查：
1. 所有服务是否正常运行
2. 环境变量配置是否正确
3. 查看日志文件了解详细错误

## 🔄 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 更新依赖
pip install -r requirements.txt

# 3. 重启服务
# 使用 Supervisor:
sudo supervisorctl restart unlock-vip-api unlock-vip-celery

# 使用 PM2:
pm2 restart all

# 使用 Docker Compose:
docker-compose down && docker-compose up -d
```

## 📝 备注

- 生产环境建议使用 HTTPS
- 定期更新依赖包
- 监控资源使用情况
- 保持日志文件大小在合理范围内
