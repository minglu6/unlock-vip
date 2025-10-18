# 🔓 Unlock-VIP - CSDN 文章下载服务

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-red.svg)](https://docs.celeryproject.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个极简的 CSDN 文章下载服务，基于 FastAPI + Celery，支持博客文章和文库文档的自动解析与下载。

> **⚡ 极简版本 v3.0**：移除了 API 认证、数据库、缓存等复杂功能，专注于核心下载能力，代码极简高效。

## ✨ 核心特性

### 🚀 异步处理
- **Celery 任务队列** - 基于 Redis 的异步任务处理
- **并发下载** - 支持同时处理多个下载请求
- **任务状态追踪** - 实时查询任务进度和结果

### 📚 多格式支持
- **博客文章** (`blog.csdn.net`) - 完整提取文章内容
- **文库文档** (`wenku.csdn.net`) - Markdown 渲染 + 语法高亮
- **格式保留** - 保持原文排版和样式
- **纯净输出** - 只保存文章核心内容

### 🧹 智能管理
- **自动文件清理** - 定期清理旧的下载文件
- **存储管理** - 自动删除过期文件释放空间
- **无需认证** - 直接调用，简单快捷

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Redis 服务器

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

**重要**：本项目使用 cookies.json 进行 CSDN 身份验证，需要手动获取 CSDN cookies。

```bash
# 复制模板文件
cp cookies.json.example cookies.json
```

编辑 `cookies.json`，填入从浏览器中获取的 CSDN cookies：

1. 在浏览器中登录 CSDN
2. 打开开发者工具（F12）
3. 进入 Application/存储 -> Cookies
4. 复制关键 cookie 值（UserToken, UserInfo, dc_sid 等）
5. 粘贴到 `cookies.json` 文件中

### 3. 启动服务

```bash
# 启动 Redis（如果未运行）
redis-server

# 启动 Celery Worker（新终端）
python celery_worker.py

# 启动 FastAPI 服务（新终端）
python run.py
```

### 4. 测试接口

访问 `http://localhost:8000/docs` 查看 API 文档。

使用 curl 测试：
```bash
curl -X POST "http://localhost:8000/api/article/submit" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://blog.csdn.net/..."}'
```

## 📖 API 文档

### 1. 提交下载任务

**端点**: `POST /api/article/submit`

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
  "status": "PENDING",
  "message": "任务已成功提交，请使用任务ID轮询状态"
}
```

### 2. 查询任务状态

**端点**: `GET /api/article/task/{task_id}/status`

**响应**:
```json
{
  "task_id": "abc-123-def",
  "status": "SUCCESS",
  "progress": 100,
  "result": {
    "success": true,
    "title": "文章标题",
    "file_size": 12345
  },
  "error": null
}
```

### 3. 获取任务结果

**端点**: `GET /api/article/task/{task_id}/result`

**响应**:
```json
{
  "task_id": "abc-123-def",
  "success": true,
  "content": "<html>...</html>",
  "file_size": 12345,
  "title": "文章标题",
  "error": null
}
```

### 4. 下载文件

**端点**: `GET /api/file/{filename}`

直接下载保存的文章文件。

## 🐳 Docker 部署

### 开发环境

```bash
# 使用 Docker Compose
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 生产环境

```bash
# 使用生产配置
docker-compose -f docker-compose.prod.yml up -d
```

## 📁 项目结构

```
unlock-vip/
├── app/                    # 应用核心代码
│   ├── api/               # API 路由
│   │   ├── article.py    # 文章下载接口
│   │   └── file.py       # 文件下载接口
│   ├── services/          # 业务服务层
│   │   ├── article_service.py  # 博客文章服务
│   │   ├── wenku_service.py    # 文库文档服务
│   │   └── file_service.py     # 文件管理服务
│   ├── tasks/             # Celery 任务
│   │   ├── article_tasks.py    # 下载任务
│   │   └── cleanup_tasks.py    # 清理任务
│   ├── core/              # 核心配置
│   │   ├── config.py     # 应用配置
│   │   └── celery_app.py # Celery配置
│   └── main.py            # FastAPI 入口
├── docs/                   # 文档
│   └── guides/            # 使用指南
├── tests/                  # 测试文件
├── userscripts/           # 浏览器用户脚本
├── cookies.json           # CSDN Cookies
├── docker-compose.yml     # 开发环境Docker配置
├── docker-compose.prod.yml # 生产环境Docker配置
└── requirements.txt       # Python 依赖
```

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

- [Claude 使用指南](CLAUDE.md) - Claude Code 使用说明
- [文档中心](docs/README.md) - 完整文档索引
- [脚本使用说明](scripts/README.md) - 实用脚本说明
- [用户脚本指南](userscripts/README_USERSCRIPT.md) - 浏览器脚本使用

## 🔧 常见问题

### 1. Cookies 失效怎么办？

Cookies 会定期失效，需要重新获取：
1. 重新登录 CSDN
2. 使用开发者工具导出新的 cookies
3. 更新 `cookies.json` 文件
4. 重启服务

### 2. Redis 连接失败？

确保 Redis 服务正在运行：
```bash
# 启动 Redis
redis-server

# 检查状态
redis-cli ping  # 应该返回 PONG
```

### 3. 下载的文章在哪里？

文章默认保存在 `downloads/` 目录下，可以通过 API 下载或直接访问文件。

## 🎯 极简版本说明

**v3.0 极简版本特点**：

✅ **保留功能**：
- FastAPI REST API
- Celery 异步任务队列
- 文章/文库下载
- 文件管理
- Cookie 认证

❌ **移除功能**：
- API Key 认证系统
- MySQL/SQLite 数据库
- Redis 结果缓存
- 请求日志记录
- 频率限制
- 自动登录
- Playwright 浏览器自动化

**优势**：
- 代码量减少约 60%
- 无需数据库
- 部署超简单
- 启动速度更快
- 资源占用更少
- 维护成本低

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
