# 🔓 unlock-vip# CS## ✨ 特性



一个基于 FastAPI + Celery 的 CSDN 文章智能下载服务，支持博客文章和文库文档的自动解析与下载。- 🚀 **异步任务队列** - 基于 Celery + Redis

- 🔓 **VIP 自动解锁** - 自动检测并解锁 VIP 文章

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)- 🔐 **API Key 认证** - 基于密钥的访问控制

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)- 📊 **请求日志记录** - 完整的 API 调用日志

[![Celery](https://img.shields.io/badge/Celery-5.4+-red.svg)](https://docs.celeryproject.org/)- ⏱️ **频率限制** - 支持分钟/小时/天级别的限流

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)- 🧹 **自动文件清理** - 定期清理旧的下载文件

- 📄 **纯净模式** - 只保存文章核心内容

## ✨ 核心特性- ⚡ **并发处理** - 支持同时处理多个下载请求

- 🎯 **简单易用** - 统一的 REST API 接口

### 🚀 异步处理一个基于 FastAPI + Celery 的 CSDN 文章下载服务，支持 VIP 文章自动解锁。

- **Celery任务队列** - 基于Redis的分布式任务处理

- **并发下载** - 支持同时处理多个下载请求## ✨ 特性

- **任务状态追踪** - 实时查询任务进度和结果

- 🚀 **异步任务队列** - 基于 Celery + Redis

### 📚 多格式支持- 🔓 **VIP 自动解锁** - 自动检测并解锁 VIP 文章

- **博客文章** (`blog.csdn.net`) - 完整提取文章内容- � **API Key 认证** - 基于密钥的访问控制

- **文库文档** (`wenku.csdn.net`) - Markdown渲染+语法高亮- 📊 **请求日志记录** - 完整的 API 调用日志

- **代码高亮** - 自动识别代码块并应用语法着色- ⏱️ **频率限制** - 支持分钟/小时/天级别的限流

- **格式保留** - 保持原文排版和样式- �📄 **纯净模式** - 只保存文章核心内容

- ⚡ **并发处理** - 支持同时处理多个下载请求

### 🔐 安全认证- 🎯 **简单易用** - 统一的 REST API 接口

- **API Key认证** - 基于密钥的访问控制

- **管理员系统** - 独立的管理员密钥管理## 🚀 快速开始

- **速率限制** - 分钟/小时/天级别的请求限流

- **请求日志** - 完整记录所有API调用### 1. 安装依赖



### 🧹 智能管理```bash

- **自动清理** - 定期清理过期下载文件pip install -r requirements.txt

- **纯净模式** - 只保存文章核心内容```

- **错误重试** - 自动重试失败的下载任务

### 2. 配置环境

## 📦 技术栈

复制 `.env.example` 为 `.env` 并配置：

| 组件 | 技术 | 版本 | 说明 |

|------|------|------|------|```env

| **Web框架** | FastAPI | 0.115+ | 高性能异步Web框架 |# MySQL 数据库配置

| **任务队列** | Celery | 5.4+ | 分布式任务队列 |DATABASE_HOST=localhost

| **消息代理** | Redis | 6.0+ | 任务broker和结果后端 |DATABASE_PORT=3306

| **数据库** | MySQL | 8.0+ | 数据持久化 |DATABASE_USER=root

| **ORM** | SQLAlchemy | 2.0+ | 数据库ORM |DATABASE_PASSWORD=your_password

| **HTML解析** | BeautifulSoup4 | 4.12+ | 网页内容提取 |DATABASE_NAME=unlock_vip

| **Markdown渲染** | Python-Markdown | 3.7+ | Markdown转HTML |

| **代码高亮** | Pygments | 2.18+ | 语法高亮 |# 管理员认证密钥（用于管理 API Keys）

ADMIN_MASTER_KEY=your_admin_master_key

## 🚀 快速开始

# CSDN 账号

### 方式一：Docker部署（推荐）CSDN_USERNAME=your_username

CSDN_PASSWORD=your_password

```bash

# 1. 克隆项目# Redis

git clone https://github.com/minglu6/unlock-vip.gitREDIS_HOST=localhost

cd unlock-vipREDIS_PORT=6379

```

# 2. 配置环境变量

cp .env.example .env**生成管理员密钥：**

# 编辑 .env 文件，配置数据库密码等

```bash

# 3. 启动服务python generate_admin_key.py

docker-compose up -d```



# 4. 生成管理员密钥**初始化数据库：**

docker-compose exec app python scripts/generate_admin_key.py

```bash

# 5. 访问API文档# 创建数据库表

# http://localhost:8000/docspython manage_db.py init

```

# 创建第一个 API Key

### 方式二：本地开发python manage_db.py create "我的密钥"

```

```bash

# 1. 安装依赖### 3. 启动服务

pip install -r requirements.txt

```bash

# 2. 配置环境# 1. 启动 Redis

cp .env.example .envdocker run -d --name unlock-vip-redis -p 6379:6379 redis:latest

# 编辑 .env 文件

# 2. 启动 Celery Worker（新终端）

# 3. 启动MySQL和Rediscelery -A app.core.celery_app worker --loglevel=info -P solo --pool=solo

# 确保MySQL和Redis服务正在运行

# 3. 启动 API 服务器（新终端）

# 4. 启动FastAPIpython run.py

python run.py```



# 5. 启动Celery Worker（新终端）### 4. 测试

celery -A celery_worker worker --loglevel=info --pool=solo

```bash

# 6. 生成API密钥python tests/test_simple.py

python scripts/generate_admin_key.py```

```

或访问 API 文档: http://localhost:8000/docs

详细说明请查看 [快速入门指南](docs/QUICK_START.md) 或 [Docker快速启动](docs/DOCKER_QUICKSTART.md)。

## 📡 API 使用

## 📖 文档

### 认证

完整文档请访问 [文档中心](docs/README.md)。

所有 API 请求都需要在 Header 中提供 API Key：

### 快速链接

```bash

| 文档 | 说明 |X-API-Key: your_api_key_here

|------|------|```

| [快速入门](docs/QUICK_START.md) | 5分钟快速部署和运行 |

| [API参考](docs/API_QUICK_REFERENCE.md) | 完整的API端点文档 |### 下载文章

| [Docker部署](docs/DOCKER_DEPLOYMENT.md) | Docker容器化部署 |

| [API认证](docs/API_AUTHENTICATION.md) | 认证系统配置 |**端点:** `POST /api/article/download`

| [示例用法](docs/example_usage.md) | 实际使用示例 |

**Headers:**

## 🎯 使用示例```

X-API-Key: your_api_key_here

### 下载博客文章Content-Type: application/json

```

```bash

# 1. 提交下载任务**请求:**

curl -X POST "http://localhost:8000/api/article/submit" \```json

  -H "X-API-Key: YOUR_API_KEY" \{

  -H "Content-Type: application/json" \    "url": "https://blog.csdn.net/xxx/article/details/123456"

  -d '{"url": "https://blog.csdn.net/username/article/details/123456"}'}

```

# 响应

{**响应:**

  "task_id": "abc123-def456-ghi789",```json

  "status": "pending",{

  "message": "任务已提交"    "success": true,

}    "content": "<html>...</html>",

    "file_size": 13152,

# 2. 查询任务状态    "title": "文章标题",

curl "http://localhost:8000/api/article/status/abc123-def456-ghi789" \    "error": null

  -H "X-API-Key: YOUR_API_KEY"}

```

# 3. 获取文章内容

curl "http://localhost:8000/api/article/result/abc123-def456-ghi789" \**cURL 示例：**

  -H "X-API-Key: YOUR_API_KEY"

``````bash

curl -X POST "http://localhost:8000/api/article/download" \

### 下载文库文档  -H "X-API-Key: your_api_key_here" \

  -H "Content-Type: application/json" \

```bash  -d '{"url": "https://blog.csdn.net/xxx/article/details/123456"}'

# 文库文档会自动应用Markdown渲染和代码高亮```

curl -X POST "http://localhost:8000/api/article/submit" \

  -H "X-API-Key: YOUR_API_KEY" \### 管理 API Keys（需要管理员权限）

  -H "Content-Type: application/json" \

  -d '{"url": "https://wenku.csdn.net/answer/3pzv32zt84"}'所有管理接口需要提供管理员密钥（X-Admin-Key）：

```

```bash

更多示例请查看 [示例用法文档](docs/example_usage.md)。# 列出所有 API Keys

curl -H "X-Admin-Key: your_admin_key" http://localhost:8000/api/admin/api-keys

## 📁 项目结构

# 创建新的 API Key

```curl -X POST "http://localhost:8000/api/admin/api-keys" \

unlock-vip/  -H "X-Admin-Key: your_admin_key" \

├── app/                          # 应用程序代码  -H "Content-Type: application/json" \

│   ├── api/                      # API路由  -d '{"name": "新密钥", "rate_limit_per_minute": 60}'

│   │   ├── admin.py             # 管理员API

│   │   └── article.py           # 文章下载API# 查看统计

│   ├── core/                     # 核心配置curl -H "X-Admin-Key: your_admin_key" \

│   │   ├── config.py            # 配置管理  http://localhost:8000/api/admin/api-keys/1/stats?days=7

│   │   └── celery_app.py        # Celery配置```

│   ├── db/                       # 数据库

│   │   ├── database.py          # 数据库连接详见：[API 认证文档](docs/API_AUTHENTICATION.md) 和 [管理员安全指南](docs/ADMIN_SECURITY.md)

│   │   └── models.py            # 数据模型

│   ├── middleware/               # 中间件## 🐳 Docker 部署

│   │   └── auth.py              # 认证中间件

│   ├── models/                   # Pydantic模型```bash

│   │   └── schemas.py           # 请求/响应模型# 使用 Docker Compose

│   ├── services/                 # 业务逻辑docker-compose up -d

│   │   ├── article_service.py   # 文章下载服务

│   │   ├── wenku_service.py     # 文库服务# 查看服务状态

│   │   ├── auth_service.py      # 认证服务docker-compose ps

│   │   └── captcha_service.py   # 验证码服务

│   ├── tasks/                    # Celery任务# 查看日志

│   │   ├── article_tasks.py     # 文章下载任务docker-compose logs -f

│   │   └── cleanup_tasks.py     # 清理任务```

│   └── main.py                   # FastAPI应用入口

│## 📚 文档

├── docs/                         # 项目文档

│   ├── README.md                 # 文档索引- [快速开始](QUICK_START.md) - 新手入门指南

│   ├── QUICK_START.md           # 快速开始- [部署指南](DEPLOYMENT.md) - 详细的生产环境部署文档

│   ├── API_QUICK_REFERENCE.md   # API参考- [Docker 部署](DOCKER_QUICKSTART.md) - Docker 快速开始

│   └── ...                       # 其他文档- [API 认证](docs/API_AUTHENTICATION.md) - API Key 认证系统说明

│- [管理员安全](docs/ADMIN_SECURITY.md) - 管理员密钥安全指南

├── scripts/                      # 工具脚本- [文件清理](docs/FILE_CLEANUP.md) - 自动文件清理系统

│   ├── README.md                 # 脚本说明- [Celery Beat](docs/CELERY_BEAT_GUIDE.md) - 定时任务配置指南

│   ├── generate_admin_key.py    # 生成管理员密钥- [验证码服务](docs/CAPTCHA_SERVICE.md) - 验证码识别服务配置

│   ├── list_api_keys.py         # 查看API密钥

│   └── manage_db.py             # 数据库管理## 🔧 生产环境

│

├── tests/                        # 测试代码### 检查环境

│   ├── test_wenku_download.py   # 文库下载测试

│   ├── test_complete_flow.py    # 完整流程测试```bash

│   └── ...python production_check.py

│```

├── docker-compose.yml            # Docker Compose配置

├── Dockerfile                    # Docker镜像构建### 部署选项

├── requirements.txt              # Python依赖

├── run.py                        # 启动脚本1. **Docker Compose**（推荐）

├── celery_worker.py             # Celery Worker   ```bash

└── README.md                     # 本文件   docker-compose up -d

```   ```



## 🔧 配置说明2. **Supervisor** (Linux)

   参考 [DEPLOYMENT.md](DEPLOYMENT.md) 中的配置

### 环境变量

3. **PM2** (Windows/Linux)

在 `.env` 文件中配置以下变量：   ```bash

   pm2 start run.py --name unlock-vip-api --interpreter python

```env   pm2 start "celery -A app.core.celery_app worker" --name unlock-vip-celery

# MySQL数据库   ```

MYSQL_HOST=localhost

MYSQL_PORT=3306## 📊 监控

MYSQL_USER=root

MYSQL_PASSWORD=your_password安装并启动 Flower:

MYSQL_DATABASE=unlock_vip

```bash

# Redispip install flower

REDIS_HOST=localhostcelery -A app.core.celery_app flower --port=5555

REDIS_PORT=6379```

REDIS_DB=0

访问: http://localhost:5555

# 管理员密钥

ADMIN_MASTER_KEY=your_secure_admin_key## 🐛 故障排查



# CSDN Cookies（可选）### Redis 连接失败

# 将cookies.json放在项目根目录

``````bash

# 检查 Redis

### Cookies配置（文库功能）docker ps | grep redis

docker logs unlock-vip-redis

文库文档下载需要CSDN登录cookies：```



1. 登录 CSDN### Worker 未处理任务

2. 使用浏览器开发者工具导出cookies

3. 保存为 `cookies.json`：```bash

# 检查 Worker 状态

```jsoncelery -A app.core.celery_app inspect active

{```

  "UserToken": "your_token_value",

  "UserName": "your_username",### 下载失败

  ...

}- 检查 CSDN 账号是否有效

```- 确认 cookies.json 文件存在

- 查看 Worker 日志了解详细错误

## 🛠️ 维护工具

## 📝 开发

### 数据库管理

### 项目结构

```bash

# 初始化数据库```

python scripts/manage_db.pyunlock-vip/

├── app/

# 查看API密钥│   ├── api/              # API 路由

python scripts/list_api_keys.py│   ├── core/             # 核心配置

│   ├── models/           # 数据模型

# 生成管理员密钥│   ├── services/         # 业务逻辑

python scripts/generate_admin_key.py│   └── tasks/            # Celery 任务

├── tests/                # 测试文件

# 生成测试密钥├── docs/                 # 文档

python scripts/generate_test_key.py└── downloads/            # 下载目录

``````



### 服务管理### 运行测试



```bash```bash

# 启动所有服务（Docker）# 简单测试

docker-compose up -dpython tests/test_simple.py



# 查看日志# Celery 客户端测试

docker-compose logs -fpython tests/test_celery_client.py

```

# 重启服务

docker-compose restart## ⚙️ 配置说明



# 停止服务### Celery 配置

docker-compose down

```编辑 `app/core/celery_app.py`:



## 📊 性能特点```python

task_time_limit=30 * 60,          # 30分钟超时

- **并发处理**: 支持多个任务同时下载worker_prefetch_multiplier=1,      # 预取任务数

- **异步非阻塞**: FastAPI异步处理，高吞吐量```

- **任务队列**: Celery分布式任务，可横向扩展

- **缓存机制**: Redis缓存，减少重复请求### API 超时配置

- **自动清理**: 定期清理过期文件，节省存储

编辑 `app/api/article.py`:

## 🔒 安全特性

```python

- ✅ API密钥认证timeout = 300  # 5分钟超时

- ✅ 速率限制保护```

- ✅ 请求日志记录

- ✅ SQL注入防护（ORM）## 🔐 安全建议

- ✅ XSS防护

- ✅ CORS配置- ✅ 不要将 `.env` 文件提交到版本控制

- ✅ 定期轮换管理员密钥（建议 90 天）

## 🤝 贡献- ✅ 只将管理员密钥分发给必要人员

- ✅ 生产环境使用 HTTPS

欢迎贡献代码、报告问题或提出建议！- ✅ 为管理接口配置 IP 白名单

- ✅ Redis 设置密码保护

1. Fork 本仓库- ✅ MySQL 使用强密码

2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)- ✅ 定期更新依赖包

3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)- ✅ 监控 API 认证失败次数

4. 推送到分支 (`git push origin feature/AmazingFeature`)

5. 开启Pull Request详见：[管理员安全指南](docs/ADMIN_SECURITY.md)



## 📄 许可证## 📄 License



本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。MIT License



## 🙏 致谢## 🤝 贡献



- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Web框架欢迎提交 Issue 和 Pull Request！

- [Celery](https://docs.celeryproject.org/) - 分布式任务队列

- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML解析---

- [Python-Markdown](https://python-markdown.github.io/) - Markdown渲染

**注意**: 本项目仅供学习交流使用，请遵守 CSDN 服务条款。

## 📞 联系方式

- **GitHub**: [@minglu6](https://github.com/minglu6)
- **Issues**: [提交问题](https://github.com/minglu6/unlock-vip/issues)
- **文档**: [docs/README.md](docs/README.md)

---

**⚠️ 免责声明**: 本项目仅供学习交流使用，请遵守CSDN的服务条款。使用本工具下载的内容版权归原作者所有。
