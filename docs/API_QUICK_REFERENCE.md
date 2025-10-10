# 🔐 API 认证快速参考

## 密钥类型

| 类型 | 用途 | Header 名称 | 获取方式 |
|------|------|-------------|----------|
| **API Key** | 调用文章下载 API | `X-API-Key` | 管理员创建 |
| **Admin Master Key** | 管理 API Keys | `X-Admin-Key` | `generate_admin_key.py` |

## 快速开始

### 1. 生成管理员密钥

```bash
python generate_admin_key.py
# 输出: ADMIN_MASTER_KEY=xxx
```

### 2. 配置 .env

```bash
echo "ADMIN_MASTER_KEY=your_key" >> .env
```

### 3. 创建 API Key

```bash
# 方法 1: 使用 CLI 工具
python manage_db.py create "我的密钥"

# 方法 2: 使用 API
curl -X POST "http://localhost:8000/api/admin/api-keys" \
  -H "X-Admin-Key: your_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "我的密钥"}'
```

## 常用命令

### 管理 API Keys

```bash
# 列出所有密钥
curl -H "X-Admin-Key: $ADMIN_KEY" http://localhost:8000/api/admin/api-keys

# 创建密钥
curl -X POST "http://localhost:8000/api/admin/api-keys" \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新密钥",
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 1000,
    "rate_limit_per_day": 10000
  }'

# 查看统计
curl -H "X-Admin-Key: $ADMIN_KEY" \
  "http://localhost:8000/api/admin/api-keys/1/stats?days=7"

# 启用/禁用密钥
curl -X PUT "http://localhost:8000/api/admin/api-keys/1/toggle" \
  -H "X-Admin-Key: $ADMIN_KEY"

# 删除密钥
curl -X DELETE "http://localhost:8000/api/admin/api-keys/1" \
  -H "X-Admin-Key: $ADMIN_KEY"
```

### 使用 API Key 下载文章

```bash
curl -X POST "http://localhost:8000/api/article/download" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://blog.csdn.net/xxx/article/details/123456"}'
```

## Python 示例

### 管理接口

```python
import requests
import os

ADMIN_KEY = os.getenv("ADMIN_MASTER_KEY")
BASE_URL = "http://localhost:8000"

# 创建 API Key
response = requests.post(
    f"{BASE_URL}/api/admin/api-keys",
    headers={
        "X-Admin-Key": ADMIN_KEY,
        "Content-Type": "application/json"
    },
    json={
        "name": "Python测试密钥",
        "rate_limit_per_minute": 60
    }
)
api_key_data = response.json()
print(f"新密钥: {api_key_data['key']}")

# 查看所有密钥
response = requests.get(
    f"{BASE_URL}/api/admin/api-keys",
    headers={"X-Admin-Key": ADMIN_KEY}
)
keys = response.json()
for key in keys:
    print(f"- {key['name']}: {key['total_requests']} 请求")
```

### 下载文章

```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000"

response = requests.post(
    f"{BASE_URL}/api/article/download",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://blog.csdn.net/xxx/article/details/123456"
    }
)

result = response.json()
if result["success"]:
    print(f"下载成功: {result['title']}")
    print(f"大小: {result['file_size']} 字节")
    # HTML 内容在 result['content'] 中
else:
    print(f"下载失败: {result['error']}")
```

## 错误处理

### 缺少 API Key

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["header", "x-api-key"],
      "msg": "Field required"
    }
  ]
}
```

**状态码**: 422

### API Key 无效

```json
{
  "detail": "无效的API密钥"
}
```

**状态码**: 401

### API Key 已过期

```json
{
  "detail": "API密钥已过期"
}
```

**状态码**: 401

### 超过频率限制

```json
{
  "detail": "超过每分钟请求限制: 60"
}
```

**状态码**: 429

### 管理员密钥错误

```json
{
  "detail": "无效的管理员密钥"
}
```

**状态码**: 403

## 数据库操作

### CLI 工具

```bash
# 初始化数据库
python manage_db.py init

# 创建 API Key
python manage_db.py create "密钥名称"

# 列出所有密钥
python manage_db.py list

# 查看统计
python manage_db.py stats
```

### 直接 SQL

```sql
-- 查看所有 API Keys
SELECT id, name, is_active, total_requests, created_at 
FROM api_keys;

-- 查看今天的请求
SELECT api_key, COUNT(*) as count, 
       SUM(success) as success_count
FROM api_request_logs 
WHERE DATE(created_at) = CURDATE()
GROUP BY api_key;

-- 查看频率限制
SELECT name, 
       rate_limit_per_minute,
       rate_limit_per_hour,
       rate_limit_per_day
FROM api_keys
WHERE is_active = 1;
```

## 环境变量

### 必需配置

```env
# 数据库
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=unlock_vip
DATABASE_PASSWORD=strong_password
DATABASE_NAME=unlock_vip

# 管理员密钥
ADMIN_MASTER_KEY=your_generated_admin_key
```

### 可选配置

```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# CSDN 账号
CSDN_USERNAME=your_username
CSDN_PASSWORD=your_password

# 验证码服务
CAPTCHA_SERVICE=mock
```

## 频率限制说明

| 时间窗口 | 默认限制 | 说明 |
|----------|---------|------|
| 每分钟 | 60 | 防止短时间爆发请求 |
| 每小时 | 1000 | 正常使用足够 |
| 每天 | 10000 | 防止滥用 |

可以在创建 API Key 时自定义：

```json
{
  "name": "高频密钥",
  "rate_limit_per_minute": 120,
  "rate_limit_per_hour": 5000,
  "rate_limit_per_day": 50000
}
```

## 监控

### 查看统计

```bash
# 7 天统计
curl -H "X-Admin-Key: $ADMIN_KEY" \
  "http://localhost:8000/api/admin/api-keys/1/stats?days=7"

# 30 天统计
curl -H "X-Admin-Key: $ADMIN_KEY" \
  "http://localhost:8000/api/admin/api-keys/1/stats?days=30"
```

### 查看日志

```bash
# 最近 100 条
curl -H "X-Admin-Key: $ADMIN_KEY" \
  "http://localhost:8000/api/admin/logs?limit=100"

# 只看失败的
curl -H "X-Admin-Key: $ADMIN_KEY" \
  "http://localhost:8000/api/admin/logs?success=false"

# 特定密钥
curl -H "X-Admin-Key: $ADMIN_KEY" \
  "http://localhost:8000/api/admin/logs?api_key=xxx"
```

## 安全最佳实践

### ✅ 应该做的

1. **定期轮换密钥** - 建议 90 天
2. **使用强密钥** - 至少 32 字节随机
3. **限制访问** - IP 白名单 + HTTPS
4. **监控异常** - 认证失败、高频请求
5. **备份数据库** - 定期备份 API Keys 和日志

### ❌ 不应该做的

1. ❌ 将密钥提交到 Git
2. ❌ 在代码中硬编码密钥
3. ❌ 共享管理员密钥
4. ❌ 使用弱密钥（如 "123456"）
5. ❌ 忽略认证失败告警

## 故障排查

### 问题：API 返回 401

**检查项**：
1. Header 中是否包含 `X-API-Key`
2. API Key 是否正确（区分大小写）
3. API Key 是否被禁用
4. API Key 是否过期

**解决**：
```bash
# 检查密钥状态
python manage_db.py list
```

### 问题：管理接口返回 403

**检查项**：
1. Header 中是否包含 `X-Admin-Key`
2. 管理员密钥是否正确
3. .env 文件中是否配置了 ADMIN_MASTER_KEY

**解决**：
```bash
# 重新生成管理员密钥
python generate_admin_key.py
# 更新 .env
# 重启服务
```

### 问题：超过频率限制

**检查项**：
1. 查看当前限制设置
2. 确认请求频率

**解决**：
```bash
# 调整限制
curl -X POST "http://localhost:8000/api/admin/api-keys" \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "高频密钥",
    "rate_limit_per_minute": 120
  }'
```

## 相关文档

- [完整 API 认证文档](API_AUTHENTICATION.md)
- [管理员安全指南](ADMIN_SECURITY.md)
- [Docker 部署指南](DOCKER_DEPLOYMENT.md)

---

**版本**: 1.0  
**更新时间**: 2025-10-02
