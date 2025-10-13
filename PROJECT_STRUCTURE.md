# 项目结构说明

## 📁 项目目录结构

```
unlock-vip/
├── app/                          # 应用核心代码
│   ├── api/                      # API 路由
│   │   ├── admin.py             # 管理员接口
│   │   ├── article.py           # 文章下载接口
│   │   └── file.py              # 文件管理接口
│   ├── core/                     # 核心配置
│   │   ├── celery_app.py        # Celery 配置
│   │   └── config.py            # 应用配置
│   ├── db/                       # 数据库
│   │   ├── database.py          # 数据库连接
│   │   └── models.py            # 数据模型
│   ├── middleware/               # 中间件
│   │   └── auth.py              # 认证中间件
│   ├── models/                   # Pydantic 模型
│   │   └── schemas.py           # API 数据模型
│   ├── services/                 # 业务服务层
│   │   ├── article_service.py   # 文章服务（简化版，仅使用 cookies）
│   │   ├── file_service.py      # 文件服务
│   │   └── wenku_service.py     # 文库服务（简化版，仅使用 cookies）
│   ├── tasks/                    # Celery 异步任务
│   │   ├── article_tasks.py     # 文章下载任务
│   │   └── cleanup_tasks.py     # 文件清理任务
│   ├── utils/                    # 工具函数
│   └── main.py                   # FastAPI 应用入口
│
├── docs/                         # 文档目录
│   ├── api/                      # API 文档
│   │   ├── API_AUTHENTICATION.md
│   │   ├── API_QUICK_REFERENCE.md
│   │   ├── FILE_DOWNLOAD_API.md
│   │   └── POSTMAN_COLLECTION.json
│   ├── deployment/               # 部署文档
│   │   ├── ALIYUN_DEPLOYMENT.md
│   │   ├── ALIYUN_PRODUCTION_DEPLOY.md
│   │   ├── DEPLOYMENT.md
│   │   ├── DEPLOYMENT_CHECKLIST.md
│   │   ├── DOCKER_DEPLOYMENT.md
│   │   ├── DOCKER_IMAGE_GUIDE.md
│   │   ├── DOCKER_QUICKSTART.md
│   │   ├── PRODUCTION_DEPLOY_README.md
│   │   └── QUICK_DEPLOY_STEPS.md
│   ├── guides/                   # 使用指南
│   │   ├── ADMIN_AUTH_IMPLEMENTATION.md
│   │   ├── ADMIN_SECURITY.md
│   │   ├── CELERY_BEAT_GUIDE.md
│   │   ├── example_usage.md
│   │   ├── FILE_CLEANUP.md
│   │   ├── FILE_CLEANUP_IMPLEMENTATION.md
│   │   ├── PROJECT_STANDARDS.md
│   │   ├── QUICK_GUIDE.md
│   │   ├── QUICK_START.md
│   │   ├── SETUP_AUTH.md
│   │   ├── THREAD_POOL_CONFIG.md
│   │   └── THREAD_POOL_FEATURE.md
│   └── README.md                 # 文档索引
│
├── downloads/                    # 下载文件存放目录
│   └── .gitkeep
│
├── nginx/                        # Nginx 配置
│   ├── conf.d/
│   └── nginx.conf
│
├── scripts/                      # 实用脚本
│   ├── generate_admin_key.py    # 生成管理员 API Key
│   ├── generate_test_key.py     # 生成测试 API Key
│   ├── list_api_keys.py         # 列出所有 API Key
│   ├── manage_db.py             # 数据库管理
│   ├── manage.sh                # 项目管理脚本
│   └── README.md                # 脚本说明
│
├── tests/                        # 测试文件
│   ├── test_admin_auth.py       # 管理员认证测试
│   ├── test_auth_system.py      # 认证系统测试
│   ├── test_cleanup.py          # 清理功能测试
│   ├── test_cleanup_direct.py   # 直接清理测试
│   ├── test_complete_flow.py    # 完整流程测试
│   ├── test_temp_dir_fix.py     # 临时目录修复测试
│   ├── test_thread_pool.py      # 线程池测试
│   └── test_wenku_download.py   # 文库下载测试
│
├── userscripts/                  # 浏览器用户脚本
│   ├── csdn_helper.js           # CSDN 助手脚本
│   ├── unlock_vip.js            # VIP 解锁脚本
│   ├── README_USERSCRIPT.md     # 用户脚本说明
│   └── USERSCRIPT_GUIDE.md      # 用户脚本指南
│
├── .dockerignore                 # Docker 忽略文件
├── .env                          # 环境变量配置
├── .env.prod                     # 生产环境配置
├── .gitignore                    # Git 忽略文件
├── API_KEY_SETUP.md             # API Key 设置指南
├── celery_worker.py             # Celery Worker 入口
├── cookies.json.example         # Cookies 模板文件
├── docker-compose.yml           # Docker Compose 配置
├── docker-compose.prod.yml      # 生产环境 Docker Compose
├── Dockerfile                    # Docker 镜像配置
├── init-db.sql                   # 数据库初始化脚本
├── nginx.conf                    # Nginx 配置文件
├── nginx.prod.conf              # 生产环境 Nginx 配置
├── PROJECT_STRUCTURE.md         # 本文件
├── README.md                     # 项目主文档
├── requirements.txt             # Python 依赖
└── run.py                        # 应用启动入口
```

## 📝 核心目录说明

### `/app` - 应用核心
包含所有业务逻辑和应用代码。

**重要变更**：
- `article_service.py` 和 `wenku_service.py` 已简化，移除了自动登录功能
- 现在仅通过 `cookies.json` 文件加载认证信息
- 移除了 `auth_service.py` 和 `captcha_service.py`（已废弃）
- 移除了 `utils/stealth_utils.py`（Playwright stealth，已证实无效）

### `/docs` - 文档
分类整理的项目文档：
- `api/` - API 接口文档
- `deployment/` - 部署相关文档
- `guides/` - 使用指南和教程

### `/scripts` - 脚本
数据库管理、API Key 生成等实用脚本。

### `/tests` - 测试
保留核心功能的测试用例，已删除与自动登录相关的测试。

### `/userscripts` - 浏览器脚本
浏览器扩展脚本和相关文档。

### `/downloads` - 下载目录
存放下载的文章和文档文件。

## 🔑 Cookies 配置

项目现在完全依赖 `cookies.json` 文件进行身份验证：

1. 复制模板文件：
   ```bash
   cp cookies.json.example cookies.json
   ```

2. 在浏览器中登录 CSDN，使用开发者工具导出 cookies

3. 编辑 `cookies.json`，填入实际的 cookie 值

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 cookies
cp cookies.json.example cookies.json
# 编辑 cookies.json 填入实际值

# 运行应用
python run.py
```

## 📚 更多文档

- [README.md](README.md) - 项目主文档
- [API_KEY_SETUP.md](API_KEY_SETUP.md) - API Key 设置
- [docs/README.md](docs/README.md) - 文档索引
- [scripts/README.md](scripts/README.md) - 脚本说明

## 🎯 简化说明

本项目已进行大幅简化：
- ❌ 移除自动登录功能
- ❌ 移除 Playwright 和 Selenium
- ❌ 移除 playwright-stealth（已证实无效）
- ❌ 移除验证码识别服务
- ✅ 仅使用 cookies.json 进行认证
- ✅ 使用 requests 库模拟浏览器请求
- ✅ 代码更简洁，性能更好
