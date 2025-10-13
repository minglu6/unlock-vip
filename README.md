# 🔓 Unlock-VIP - CSDN 文章下载服务

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-red.svg)](https://docs.celeryproject.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 FastAPI + Celery 的 CSDN 文章智能下载服务，支持博客文章和文库文档的自动解析与下载。

> **⚡ 简化版本**：本项目已删繁就简，移除了自动登录、Playwright 等复杂功能，仅使用 cookies.json 进行认证，代码更简洁高效。

## ✨ 核心特性

### 🚀 异步处理
- **Celery 任务队列** - 基于 Redis 的分布式任务处理
- **并发下载** - 支持同时处理多个下载请求
- **任务状态追踪** - 实时查询任务进度和结果

### 📚 多格式支持
- **博客文章** (`blog.csdn.net`) - 完整提取文章内容
- **文库文档** (`wenku.csdn.net`) - Markdown 渲染 + 语法高亮
- **VIP 解锁** - 自动检测并尝试解锁 VIP 文章
- **格式保留** - 保持原文排版和样式

### 🔐 安全认证
- **API Key 认证** - 基于密钥的访问控制
- **管理员系统** - 独立的管理员密钥管理
- **请求日志** - 完整的 API 调用记录
- **频率限制** - 支持分钟/小时/天级别的限流

### 🧹 智能管理
- **自动文件清理** - 定期清理旧的下载文件
- **存储管理** - 自动删除过期文件释放空间
- **纯净模式** - 只保存文章核心内容，去除广告

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Redis 服务器
- MySQL 数据库（可选，用于生产环境）

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-repo/unlock-vip.git
cd unlock-vip

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 Cookies

**重要**：本项目使用 cookies.json 进行身份验证，需要手动获取 CSDN cookies。

```bash
# 复制模板文件
cp cookies.json.example cookies.json
```

然后编辑 `cookies.json`，填入从浏览器中获取的 CSDN cookies：

1. 在浏览器中登录 CSDN
2. 打开开发者工具（F12）
3. 进入 Application/存储 -> Cookies
4. 复制关键 cookie 值（UserToken, UserInfo 等）
5. 粘贴到 `cookies.json` 文件中

`cookies.json` 格式示例：
```json
{
  "UserToken": "your_token_here",
  "UserInfo": "your_info_here",
  "dc_sid": "your_sid_here"
}
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env  # 如果没有 .env.example，手动创建 .env

# 编辑 .env 文件
nano .env
```

基本配置示例：
```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 数据库配置（可选）
DATABASE_URL=sqlite:///./unlock_vip.db

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. 生成 API Key

```bash
# 生成管理员 API Key
python scripts/generate_admin_key.py

# 生成普通测试 Key
python scripts/generate_test_key.py
```

### 5. 启动服务

```bash
# 启动 Redis（如果未运行）
redis-server

# 启动 Celery Worker
python celery_worker.py

# 启动 FastAPI 服务（新终端）
python run.py
```

### 6. 测试接口

访问 `http://localhost:8000/docs` 查看 API 文档并测试。

或使用 curl：
```bash
curl -X POST "http://localhost:8000/api/download" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://blog.csdn.net/..."}'
```

## 📖 API 文档

### 下载文章

**端点**: `POST /api/download`

**请求头**:
```
X-API-Key: your_api_key_here
```

**请求体**:
```json
{
  "url": "https://blog.csdn.net/username/article/details/123456"
}
```

**响应**:
```json
{
  "task_id": "abc-123-def",
  "status": "pending",
  "message": "任务已创建"
}
```

### 查询任务状态

**端点**: `GET /api/task/{task_id}`

**响应**:
```json
{
  "task_id": "abc-123-def",
  "status": "SUCCESS",
  "result": {
    "file_path": "/downloads/article.html",
    "file_size": 12345,
    "title": "文章标题"
  }
}
```

### 下载文件

**端点**: `GET /api/file/{filename}`

直接下载保存的文章文件。

## 🐳 Docker 部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

详细部署文档请参考：
- [Docker 部署指南](docs/deployment/DOCKER_DEPLOYMENT.md)
- [生产环境部署](docs/deployment/PRODUCTION_DEPLOY_README.md)

## 📁 项目结构

```
unlock-vip/
├── app/                    # 应用核心代码
│   ├── api/               # API 路由
│   ├── services/          # 业务服务层（简化版）
│   ├── tasks/             # Celery 任务
│   └── main.py            # FastAPI 入口
├── docs/                   # 文档
│   ├── api/               # API 文档
│   ├── deployment/        # 部署文档
│   └── guides/            # 使用指南
├── scripts/                # 实用脚本
├── tests/                  # 测试文件
├── userscripts/           # 浏览器用户脚本
├── cookies.json.example   # Cookies 模板
└── requirements.txt       # Python 依赖
```

详细结构说明：[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🛠️ 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_article_service.py

# 查看覆盖率
pytest --cov=app tests/
```

### 代码规范

项目使用以下工具保证代码质量：
- **Black** - 代码格式化
- **Flake8** - 代码检查
- **MyPy** - 类型检查

```bash
# 格式化代码
black app/

# 检查代码
flake8 app/

# 类型检查
mypy app/
```

## 📚 文档索引

- [API 认证指南](API_KEY_SETUP.md)
- [项目结构说明](PROJECT_STRUCTURE.md)
- [快速开始指南](docs/guides/QUICK_START.md)
- [API 快速参考](docs/api/API_QUICK_REFERENCE.md)
- [部署检查清单](docs/deployment/DEPLOYMENT_CHECKLIST.md)
- [脚本使用说明](scripts/README.md)

## 🔧 常见问题

### 1. Cookies 失效怎么办？

Cookies 会定期失效，需要重新获取：
1. 重新登录 CSDN
2. 使用开发者工具导出新的 cookies
3. 更新 `cookies.json` 文件
4. 重启服务

### 2. 如何处理 VIP 文章？

项目会自动检测 VIP 文章并尝试解锁。如果您的账号没有 VIP 权限，解锁可能失败，此时会下载锁定状态的内容。

### 3. Redis 连接失败？

确保 Redis 服务正在运行：
```bash
# Linux/Mac
redis-server

# 检查状态
redis-cli ping  # 应该返回 PONG
```

### 4. 下载的文章在哪里？

文章默认保存在 `downloads/` 目录下，可以通过 API 下载或直接访问文件。

## 🎯 简化说明

**本版本已进行大幅简化**：

✅ **保留功能**：
- FastAPI REST API
- Celery 异步任务队列
- 文章/文库下载
- API Key 认证
- 文件管理

❌ **移除功能**：
- 自动登录（改为手动配置 cookies）
- Playwright 浏览器自动化
- Selenium
- playwright-stealth（已证实无效）
- 验证码识别服务

**优势**：
- 代码量减少约 50%
- 无需安装浏览器驱动
- 启动速度更快
- 资源占用更少
- 更易于维护

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [Celery](https://docs.celeryproject.org/) - 分布式任务队列
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析

## ⚠️ 免责声明

本项目仅供学习和研究使用，请勿用于商业用途。使用本工具下载的内容版权归原作者所有，请尊重知识产权。

---

**Star ⭐ 本项目如果觉得有帮助！**
