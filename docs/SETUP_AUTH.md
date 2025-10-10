# 🚀 API 认证系统设置指南

## 第一步：配置环境变量

复制 `.env.example` 到 `.env` 并配置数据库信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# MySQL 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_password
DATABASE_NAME=unlock_vip
```

## 第二步：创建数据库

连接到 MySQL 并创建数据库：

```sql
CREATE DATABASE unlock_vip CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 第三步：安装依赖

```bash
pip install -r requirements.txt
```

## 第四步：初始化数据库表

```bash
python manage_db.py init
```

这将创建以下表：
- `api_keys` - API 密钥表
- `api_request_logs` - 请求日志表

## 第五步：创建第一个 API Key

```bash
python manage_db.py create "我的第一个密钥"
```

记录输出的 API Key，例如：
```
API Key: Abc123XYZ_your_actual_key_here_456
```

## 第六步：启动服务

### 启动 FastAPI 服务

```bash
# 终端 1
uvicorn app.main:app --reload --port 8000
```

### 启动 Celery Worker

```bash
# 终端 2
celery -A app.core.celery_app worker --loglevel=info -P solo
```

### 确保 Redis 运行

```bash
# Docker 方式
docker run -d -p 6379:6379 --name redis redis:alpine

# 或者使用 docker-compose
docker-compose up -d redis
```

## 第七步：测试 API

使用你的 API Key 测试：

```bash
curl -X POST "http://localhost:8000/api/article/download" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "url": "https://blog.csdn.net/xxx/article/details/xxx"
  }'
```

或运行测试脚本：

```bash
python tests/test_auth_system.py
```

## 常见问题

### 1. 数据库连接失败

**错误**: `Can't connect to MySQL server`

**解决**:
- 检查 MySQL 是否运行：`mysql -u root -p`
- 验证 `.env` 中的数据库配置
- 确保数据库用户有权限

### 2. 导入错误

**错误**: `Import "sqlalchemy" could not be resolved`

**解决**:
```bash
pip install sqlalchemy pymysql cryptography
```

### 3. 表不存在

**错误**: `Table 'unlock_vip.api_keys' doesn't exist`

**解决**:
```bash
python manage_db.py init
```

### 4. API Key 无效

**错误**: `401: 无效的API密钥`

**解决**:
- 检查 Header 名称是否为 `X-API-Key`
- 确认 API Key 没有多余的空格
- 用 `python manage_db.py list` 查看有效的密钥

## 下一步

- 📖 阅读 [API_AUTHENTICATION.md](API_AUTHENTICATION.md) 了解完整功能
- 🔧 使用管理接口进行密钥管理
- 📊 查看统计信息：`python manage_db.py stats`
- 🔍 查看请求日志了解使用情况

## Docker 部署

如果使用 Docker，在 `docker-compose.yml` 中添加 MySQL：

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DATABASE_PASSWORD}
      MYSQL_DATABASE: ${DATABASE_NAME}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mysql_data:
```

然后启动：

```bash
docker-compose up -d
```

等待 MySQL 启动后初始化数据库：

```bash
docker-compose exec web python manage_db.py init
docker-compose exec web python manage_db.py create "生产密钥"
```
