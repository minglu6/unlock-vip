# 🚀 快速访问指南

unlock-vip项目的快速导航。

## 📚 文档导航

### 新手入门
- **[主README](README.md)** - 项目概览和快速开始
- **[快速入门](docs/QUICK_START.md)** - 5分钟上手指南
- **[Docker快速启动](docs/DOCKER_QUICKSTART.md)** - Docker一键部署

### 完整文档
- **[文档中心](docs/README.md)** - 所有文档的索引和分类

## 🛠️ 常用操作

### 启动服务

```bash
# Docker方式（推荐）
docker-compose up -d

# 本地开发
python run.py                                    # 启动FastAPI
celery -A celery_worker worker --loglevel=info  # 启动Celery（新终端）
```

### 密钥管理

```bash
# 生成管理员密钥
python scripts/generate_admin_key.py

# 查看所有密钥
python scripts/list_api_keys.py

# 生成测试密钥
python scripts/generate_test_key.py
```

### 数据库操作

```bash
# 初始化数据库
python scripts/manage_db.py

# 查看数据库状态
python scripts/manage_db.py --status
```

### 运行测试

```bash
# 测试文库下载
python tests/test_wenku_download.py

# 测试完整流程
python tests/test_complete_flow.py

# 测试认证系统
python tests/test_auth_system.py
```

## 📖 API使用

### 提交下载任务

```bash
curl -X POST "http://localhost:8000/api/article/submit" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://blog.csdn.net/user/article/details/123"}'
```

### 查询任务状态

```bash
curl "http://localhost:8000/api/article/status/TASK_ID" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 获取文章内容

```bash
curl "http://localhost:8000/api/article/result/TASK_ID" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 查看API文档

访问: http://localhost:8000/docs

## 🔍 查找内容

### 按主题查找文档

| 主题 | 文档位置 |
|------|---------|
| **API使用** | [docs/API_QUICK_REFERENCE.md](docs/API_QUICK_REFERENCE.md) |
| **API认证** | [docs/API_AUTHENTICATION.md](docs/API_AUTHENTICATION.md) |
| **Docker部署** | [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) |
| **阿里云部署** | [docs/ALIYUN_DEPLOYMENT.md](docs/ALIYUN_DEPLOYMENT.md) |
| **文件清理** | [docs/FILE_CLEANUP.md](docs/FILE_CLEANUP.md) |
| **Celery任务** | [docs/CELERY_BEAT_GUIDE.md](docs/CELERY_BEAT_GUIDE.md) |
| **管理员系统** | [docs/ADMIN_SECURITY.md](docs/ADMIN_SECURITY.md) |
| **文库集成** | [docs/WENKU_INTEGRATION_SUMMARY.md](docs/WENKU_INTEGRATION_SUMMARY.md) |

### 按任务查找工具

| 任务 | 工具位置 |
|------|---------|
| **生成密钥** | [scripts/generate_admin_key.py](scripts/generate_admin_key.py) |
| **查看密钥** | [scripts/list_api_keys.py](scripts/list_api_keys.py) |
| **管理数据库** | [scripts/manage_db.py](scripts/manage_db.py) |
| **测试文库** | [tests/test_wenku_download.py](tests/test_wenku_download.py) |
| **测试流程** | [tests/test_complete_flow.py](tests/test_complete_flow.py) |

## 🆘 遇到问题？

### 常见问题

1. **服务启动失败**
   - 检查MySQL和Redis是否运行
   - 查看`.env`配置是否正确
   - 检查端口8000是否被占用

2. **API密钥无效**
   - 运行 `python scripts/list_api_keys.py` 查看所有密钥
   - 确认密钥状态为"启用"
   - 检查速率限制是否超出

3. **文章下载失败**
   - 确认URL格式正确
   - 检查Celery Worker是否运行
   - 查看日志: `docker-compose logs -f celery`

4. **文库功能不可用**
   - 确认 `cookies.json` 文件存在
   - 检查cookies是否过期
   - 重新登录CSDN并导出cookies

### 获取帮助

1. **查看文档**: [docs/README.md](docs/README.md)
2. **查看示例**: [docs/example_usage.md](docs/example_usage.md)
3. **查看日志**: `docker-compose logs -f`
4. **提交Issue**: https://github.com/minglu6/unlock-vip/issues

## 📁 项目规范

如果你要参与开发，请阅读：
- **[项目规范](PROJECT_STANDARDS.md)** - 代码和文档组织规范
- **[整理总结](PROJECT_CLEANUP_SUMMARY.md)** - 项目结构说明

## 🔗 重要链接

| 链接 | 说明 |
|------|------|
| [README.md](README.md) | 项目主页 |
| [docs/README.md](docs/README.md) | 文档中心 |
| [scripts/README.md](scripts/README.md) | 工具说明 |
| [PROJECT_STANDARDS.md](PROJECT_STANDARDS.md) | 项目规范 |
| [PROJECT_CLEANUP_SUMMARY.md](PROJECT_CLEANUP_SUMMARY.md) | 整理总结 |

## 📊 项目结构概览

```
unlock-vip/
├── 📘 README.md                      # 从这里开始
├── 📁 docs/                          # 所有文档
│   └── 📚 README.md                  # 文档索引
├── 🛠️ scripts/                      # 工具脚本
│   └── 📖 README.md                  # 脚本说明
├── 🧪 tests/                        # 测试代码
├── 💻 app/                          # 应用代码
├── 🐳 docker-compose.yml            # Docker配置
└── 📦 requirements.txt              # Python依赖
```

---

**💡 提示**: 将此文件加入书签，方便快速访问！
