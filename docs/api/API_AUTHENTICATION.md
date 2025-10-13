# API 认证和请求记录系统

本文档说明如何使用新的 API 认证系统。

## 🔑 系统特性

1. **API Key 认证** - 所有请求需要在 Header 中提供 API Key
2. **请求日志记录** - 自动记录每次 API 调用
3. **频率限制** - 支持按分钟/小时/天的请求限制
4. **统计分析** - 完整的使用统计和报表
5. **密钥管理** - 创建、查看、启用/禁用 API Key

## 📦 环境准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖包:
- `sqlalchemy==2.0.23` - ORM 框架
- `pymysql==1.1.0` - MySQL 驱动
- `cryptography==41.0.7` - 加密支持

### 2. 配置 MySQL 数据库

在 `.env` 文件中配置数据库连接:

```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_password
DATABASE_NAME=unlock_vip
```

### 3. 创建数据库

```sql
CREATE DATABASE unlock_vip CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 初始化数据库表

```bash
python manage_db.py init
```

## 🚀 快速开始

### 1. 创建 API Key

```bash
# 创建基础密钥
python manage_db.py create "测试密钥"

# 创建指定用户ID的密钥
python manage_db.py create "生产密钥" --user-id user123

# 创建有过期时间的密钥（365天后过期）
python manage_db.py create "临时密钥" --user-id user456 --expires 365
```

创建成功后会显示完整的 API Key，请妥善保存！

### 2. 使用 API

所有请求需要在 Header 中携带 `X-API-Key`:

```bash
curl -X POST "http://localhost:8000/api/article/download" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "url": "https://blog.csdn.net/xxx/article/details/xxx"
  }'
```

Python 示例:

```python
import requests

headers = {
    "X-API-Key": "your_api_key_here"
}

data = {
    "url": "https://blog.csdn.net/xxx/article/details/xxx"
}

response = requests.post(
    "http://localhost:8000/api/article/download",
    headers=headers,
    json=data
)

print(response.json())
```

### 3. 查看 API Keys

```bash
# 列出所有密钥
python manage_db.py list

# 查看系统统计
python manage_db.py stats
```

## 📊 管理接口

系统提供了完整的管理 API，可以通过 HTTP 接口管理密钥。

### 创建 API Key

```http
POST /api/admin/api-keys
Content-Type: application/json

{
  "name": "我的密钥",
  "user_id": "user123",
  "rate_limit_per_minute": 60,
  "rate_limit_per_hour": 1000,
  "rate_limit_per_day": 10000,
  "expires_days": 365,
  "description": "用于生产环境"
}
```

### 列出所有 API Keys

```http
GET /api/admin/api-keys?skip=0&limit=100&is_active=true
```

### 查看密钥详情

```http
GET /api/admin/api-keys/{key_id}
```

### 启用/禁用密钥

```http
PUT /api/admin/api-keys/{key_id}/toggle
```

### 删除密钥

```http
DELETE /api/admin/api-keys/{key_id}
```

### 查看密钥统计

```http
GET /api/admin/api-keys/{key_id}/stats?days=7
```

### 查看请求日志

```http
GET /api/admin/logs?skip=0&limit=100&days=7&success=true
```

## 🗄️ 数据库结构

### api_keys 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| key | VARCHAR(64) | API 密钥（唯一） |
| name | VARCHAR(100) | 密钥名称 |
| user_id | VARCHAR(50) | 用户ID |
| is_active | BOOLEAN | 是否启用 |
| rate_limit_per_minute | INT | 每分钟限制 |
| rate_limit_per_hour | INT | 每小时限制 |
| rate_limit_per_day | INT | 每天限制 |
| total_requests | BIGINT | 总请求数 |
| last_used_at | DATETIME | 最后使用时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| expires_at | DATETIME | 过期时间 |
| description | TEXT | 备注 |

### api_request_logs 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| api_key | VARCHAR(64) | 使用的密钥 |
| user_id | VARCHAR(50) | 用户ID |
| endpoint | VARCHAR(200) | 请求端点 |
| method | VARCHAR(10) | 请求方法 |
| url | TEXT | 文章URL |
| status_code | INT | 响应状态码 |
| success | BOOLEAN | 是否成功 |
| error_message | TEXT | 错误信息 |
| processing_time | INT | 处理时间（毫秒） |
| response_size | BIGINT | 响应大小（字节） |
| ip_address | VARCHAR(45) | 客户端IP |
| user_agent | TEXT | User Agent |
| created_at | DATETIME | 创建时间 |

## 🔒 频率限制

系统支持三个维度的频率限制：

1. **每分钟限制** (rate_limit_per_minute)
   - 默认: 60 次/分钟
   - 防止突发高频请求

2. **每小时限制** (rate_limit_per_hour)
   - 默认: 1000 次/小时
   - 控制持续负载

3. **每天限制** (rate_limit_per_day)
   - 默认: 10000 次/天
   - 总量控制

超过限制时返回 429 状态码：

```json
{
  "detail": "超过每分钟请求限制（60次）"
}
```

## 📈 统计查询示例

### SQL 查询今天的请求统计

```sql
SELECT 
  api_key,
  COUNT(*) as total_requests,
  SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
  AVG(processing_time) as avg_processing_time,
  SUM(response_size) as total_data_transferred
FROM api_request_logs
WHERE DATE(created_at) = CURDATE()
GROUP BY api_key;
```

### 查询最活跃的用户

```sql
SELECT 
  user_id,
  COUNT(*) as request_count,
  MAX(created_at) as last_request
FROM api_request_logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY user_id
ORDER BY request_count DESC
LIMIT 10;
```

### 查询错误率最高的端点

```sql
SELECT 
  endpoint,
  COUNT(*) as total,
  SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures,
  (SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) / COUNT(*)) * 100 as error_rate
FROM api_request_logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY endpoint
ORDER BY error_rate DESC;
```

## 🛡️ 安全建议

1. **保护好 API Key** - 不要在客户端代码中硬编码
2. **使用 HTTPS** - 生产环境必须使用 HTTPS
3. **定期轮换密钥** - 设置合理的过期时间
4. **监控异常** - 关注频繁失败的请求
5. **限制访问** - 根据实际需求调整频率限制
6. **管理接口保护** - 生产环境需要为管理接口添加额外认证

## 🔧 Docker Compose 更新

如果使用 Docker 部署，需要在 `docker-compose.yml` 中添加 MySQL 服务：

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: unlock_vip
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

## 📝 错误码说明

- `401` - 认证失败（无效的 API Key、已禁用、已过期）
- `429` - 超过频率限制
- `400` - 请求参数错误
- `500` - 服务器内部错误
- `504` - 任务处理超时

## 🎯 最佳实践

1. **为不同环境创建不同的密钥** - 开发、测试、生产分离
2. **合理设置频率限制** - 根据服务器性能和用户需求调整
3. **定期检查日志** - 发现异常使用模式
4. **监控密钥使用情况** - 及时发现滥用
5. **备份数据库** - 定期备份请求日志和密钥信息
