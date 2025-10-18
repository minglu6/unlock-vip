# 🔓 Unlock-VIP - CSDN 文章下载服务

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个极简的 CSDN 文章下载服务，基于 FastAPI + ThreadPoolExecutor，支持博客文章和文库文档的自动解析与下载。

> **⚡ 精简版本 v4.0**：移除了 Celery、Redis、Docker 等复杂依赖，专注于核心下载能力，单进程运行，代码极简高效。

## ✨ 核心特性

### 🚀 异步处理
- **ThreadPoolExecutor** - 基于 Python 内置线程池的异步任务处理
- **并发下载** - 支持同时处理多个下载请求
- **任务状态追踪** - 实时查询任务进度和结果
- **内存存储** - 任务状态存储在内存中，无需外部依赖

### 📚 多格式支持
- **博客文章** (`blog.csdn.net`) - 完整提取文章内容
- **文库文档** (`wenku.csdn.net`) - Markdown 渲染 + 语法高亮
- **格式保留** - 保持原文排版和样式
- **纯净输出** - 只保存文章核心内容

### 🧹 极简架构
- **单进程运行** - 无需额外的 worker 进程
- **无外部依赖** - 无需 Redis、MySQL 等服务
- **即开即用** - 一条命令启动服务
- **无需认证** - 直接调用，简单快捷

## 🚀 快速开始

### 前置要求

- Python 3.9+

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
# 启动 FastAPI 服务（单进程）
python run.py

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
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
│   │   └── file_service.py     # 文件管理和线程池
│   ├── models/            # 数据模型
│   │   └── schemas.py    # Pydantic 模型
│   ├── core/              # 核心配置
│   │   └── config.py     # 应用配置
│   └── main.py            # FastAPI 入口
├── tests/                  # 测试文件
├── userscripts/           # 浏览器用户脚本
├── cookies.json           # CSDN Cookies
├── .env                   # 环境配置
└── requirements.txt       # Python 依赖
```

## 🛠️ 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_thread_pool.py

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
- [用户脚本指南](userscripts/README_USERSCRIPT.md) - 浏览器脚本使用

## 🔧 常见问题

### 1. Cookies 失效怎么办？

Cookies 会定期失效，需要重新获取：
1. 重新登录 CSDN
2. 使用开发者工具导出新的 cookies
3. 更新 `cookies.json` 文件
4. 重启服务

### 2. 下载的文章在哪里？

文章默认保存在 `downloads/` 目录下，可以通过 API 下载或直接访问文件。

### 3. 如何调整并发数？

在 `.env` 文件中设置：
```
THREAD_POOL_WORKERS=4  # 默认 4 个工作线程
```

## 🎯 精简版本说明

**v4.0 精简版本特点**：

✅ **保留功能**：
- FastAPI REST API
- ThreadPoolExecutor 异步任务
- 文章/文库下载
- 文件管理
- Cookie 认证

❌ **移除功能**：
- Celery + Redis
- Docker 配置
- MySQL/SQLite 数据库
- API Key 认证系统
- 请求日志记录
- 频率限制
- 自动登录
- Playwright 浏览器自动化

**优势**：
- 代码量减少约 70%
- 无需任何外部服务（Redis、MySQL）
- 部署极其简单（一条命令）
- 启动速度快
- 资源占用极少
- 维护成本低
- 单进程运行

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
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML 解析

## ⚠️ 免责声明

本项目仅供学习和研究使用，请勿用于商业用途。使用本工具下载的内容版权归原作者所有，请尊重知识产权。

---

**Star ⭐ 本项目如果觉得有帮助！**
