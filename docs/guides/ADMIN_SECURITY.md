# 🔐 管理员认证安全指南

## 概述

为了保护 API 密钥管理接口，系统实现了基于管理员主密钥（Admin Master Key）的认证机制。

## 安全问题

### 问题描述

原先的管理接口（创建/列表/删除 API Key）没有任何认证保护，存在以下风险：

- ❌ 任何人都可以创建 API Key
- ❌ 任何人都可以查看所有 API Key
- ❌ 任何人都可以删除或禁用 API Key
- ❌ 任何人都可以查看请求日志和统计数据

### 解决方案

实现了基于 **管理员主密钥（ADMIN_MASTER_KEY）** 的认证机制：

- ✅ 所有管理接口都需要提供管理员密钥
- ✅ 密钥存储在环境变量中，不在数据库
- ✅ 通过 HTTP Header (`X-Admin-Key`) 传递
- ✅ 认证失败返回 403 Forbidden

## 快速开始

### 1. 生成管理员密钥

运行生成脚本：

```bash
# Python 环境
python generate_admin_key.py

# 或直接使用 Python 命令
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

输出示例：
```
============================================================
🔐 管理员主密钥已生成
============================================================

密钥: X9kL2mP4nQ8rT6vY3wZ7aB5cD1eF0gH9iJ4kL8mN2oP6qR3sT7uV1wX5yZ9aB3cD

请将此密钥添加到 .env 文件中：

ADMIN_MASTER_KEY=X9kL2mP4nQ8rT6vY3wZ7aB5cD1eF0gH9iJ4kL8mN2oP6qR3sT7uV1wX5yZ9aB3cD

⚠️  安全提示：
1. 请妥善保管此密钥，不要泄露给他人
2. 不要将此密钥提交到 Git 仓库
3. 定期更换密钥以提高安全性
4. 生产环境建议使用更长的密钥
============================================================
```

### 2. 配置环境变量

将生成的密钥添加到 `.env` 文件：

```bash
# .env
ADMIN_MASTER_KEY=X9kL2mP4nQ8rT6vY3wZ7aB5cD1eF0gH9iJ4kL8mN2oP6qR3sT7uV1wX5yZ9aB3cD
```

### 3. 重启服务

```bash
# 本地开发
python run.py

# Docker
docker-compose restart web
```

## API 使用方式

### 受保护的管理接口

所有管理接口现在都需要 `X-Admin-Key` header：

| 接口 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 创建 API Key | POST | `/admin/api-keys` | 创建新的 API 密钥 |
| 列出 API Key | GET | `/admin/api-keys` | 查看所有 API 密钥 |
| 获取 API Key | GET | `/admin/api-keys/{id}` | 获取指定密钥详情 |
| 启用/禁用 | PUT | `/admin/api-keys/{id}/toggle` | 切换密钥状态 |
| 删除 API Key | DELETE | `/admin/api-keys/{id}` | 删除密钥 |
| 获取统计 | GET | `/admin/api-keys/{id}/stats` | 获取密钥统计 |
| 查看日志 | GET | `/admin/logs` | 查看请求日志 |

### 调用示例

#### cURL

```bash
# 创建 API Key
curl -X POST "http://localhost:8000/admin/api-keys" \
  -H "X-Admin-Key: your_admin_master_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试密钥",
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 1000,
    "rate_limit_per_day": 10000
  }'

# 列出所有 API Key
curl -X GET "http://localhost:8000/admin/api-keys" \
  -H "X-Admin-Key: your_admin_master_key_here"

# 查看统计
curl -X GET "http://localhost:8000/admin/api-keys/1/stats?days=7" \
  -H "X-Admin-Key: your_admin_master_key_here"
```

#### Python (requests)

```python
import requests

ADMIN_KEY = "your_admin_master_key_here"
BASE_URL = "http://localhost:8000"

headers = {
    "X-Admin-Key": ADMIN_KEY,
    "Content-Type": "application/json"
}

# 创建 API Key
response = requests.post(
    f"{BASE_URL}/admin/api-keys",
    headers=headers,
    json={
        "name": "测试密钥",
        "rate_limit_per_minute": 60,
        "rate_limit_per_hour": 1000,
        "rate_limit_per_day": 10000
    }
)
print(response.json())

# 列出 API Keys
response = requests.get(
    f"{BASE_URL}/admin/api-keys",
    headers=headers
)
print(response.json())
```

#### Postman

1. **设置环境变量**
   - 添加变量 `admin_key`: `your_admin_master_key_here`

2. **配置 Headers**
   - Key: `X-Admin-Key`
   - Value: `{{admin_key}}`

3. **发送请求**
   - 选择对应的 HTTP 方法
   - 输入 URL 和参数
   - 点击 Send

### 错误响应

#### 缺少管理员密钥

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["header", "x-admin-key"],
      "msg": "Field required"
    }
  ]
}
```

HTTP 状态码: `422 Unprocessable Entity`

#### 管理员密钥错误

```json
{
  "detail": "无效的管理员密钥"
}
```

HTTP 状态码: `403 Forbidden`

#### 服务器未配置密钥

```json
{
  "detail": "服务器未配置管理员密钥，请联系系统管理员"
}
```

HTTP 状态码: `500 Internal Server Error`

## 安全最佳实践

### 密钥管理

1. **生成强密钥**
   ```bash
   # 使用 32 字节（推荐）
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # 使用 64 字节（更安全）
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

2. **安全存储**
   - ✅ 存储在环境变量中
   - ✅ 使用 `.env` 文件（本地开发）
   - ✅ 使用密钥管理服务（生产环境，如 AWS Secrets Manager）
   - ❌ 不要硬编码在代码中
   - ❌ 不要提交到 Git 仓库

3. **定期轮换**
   - 建议每 90 天更换一次
   - 发生安全事件时立即更换
   - 离职员工权限变更时更换

### 访问控制

1. **最小权限原则**
   - 只将管理员密钥分发给必要人员
   - 记录密钥的分发情况

2. **审计日志**
   - 监控管理接口的调用
   - 设置异常告警

3. **网络隔离**
   - 生产环境限制管理接口的访问 IP
   - 使用 VPN 或跳板机访问

### 生产环境配置

#### Nginx 反向代理保护

```nginx
# 只允许特定 IP 访问管理接口
location /admin/ {
    allow 192.168.1.0/24;  # 内网 IP
    allow 10.0.0.0/8;       # VPN IP
    deny all;
    
    proxy_pass http://backend;
}
```

#### 防火墙规则

```bash
# iptables 示例
iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

#### Docker 环境

```yaml
# docker-compose.prod.yml
services:
  web:
    environment:
      - ADMIN_MASTER_KEY=${ADMIN_MASTER_KEY}
    # 不暴露管理端口到公网
    expose:
      - "8000"
```

### 密钥轮换步骤

1. **生成新密钥**
   ```bash
   python generate_admin_key.py
   ```

2. **更新环境变量**
   ```bash
   # .env
   ADMIN_MASTER_KEY=new_key_here
   ```

3. **重启服务**
   ```bash
   docker-compose restart web
   ```

4. **通知团队成员**
   - 更新所有客户端配置
   - 更新 Postman 环境变量
   - 更新自动化脚本

5. **验证**
   ```bash
   # 测试新密钥
   curl -H "X-Admin-Key: new_key" http://localhost:8000/admin/api-keys
   ```

## 监控和告警

### 建议监控指标

1. **认证失败次数**
   - 短时间内多次 403 错误
   - 可能是攻击行为

2. **管理操作频率**
   - 异常高频的密钥创建
   - 批量删除操作

3. **访问来源**
   - 未知 IP 地址访问
   - 非工作时间访问

### 告警配置示例

```python
# 监控脚本示例
import requests
from datetime import datetime, timedelta

def check_admin_access():
    # 获取最近 1 小时的日志
    response = requests.get(
        "http://localhost:8000/admin/logs",
        headers={"X-Admin-Key": "your_admin_key"},
        params={"endpoint": "/admin/api-keys", "hours": 1}
    )
    
    logs = response.json()
    
    # 检查失败次数
    failed_count = sum(1 for log in logs if not log["success"])
    
    if failed_count > 10:
        send_alert(f"管理接口认证失败次数过多: {failed_count}")
```

## 故障排查

### 问题：提示"服务器未配置管理员密钥"

**原因**: `.env` 文件中缺少 `ADMIN_MASTER_KEY` 配置

**解决**:
1. 生成密钥: `python generate_admin_key.py`
2. 添加到 `.env` 文件
3. 重启服务

### 问题：提示"无效的管理员密钥"

**原因**: HTTP Header 中的密钥与服务器配置不匹配

**解决**:
1. 检查 `.env` 文件中的 `ADMIN_MASTER_KEY`
2. 检查请求中的 `X-Admin-Key` header
3. 确保两者完全一致（区分大小写）

### 问题：Docker 环境下密钥不生效

**原因**: 环境变量未传递到容器

**解决**:
```yaml
# docker-compose.yml
services:
  web:
    environment:
      - ADMIN_MASTER_KEY=${ADMIN_MASTER_KEY}
```

确保宿主机 `.env` 文件中配置了 `ADMIN_MASTER_KEY`

## 迁移指南

### 从无认证迁移到有认证

1. **备份现有 API Keys**
   ```bash
   # 导出现有密钥（在添加认证前）
   curl http://localhost:8000/admin/api-keys > api_keys_backup.json
   ```

2. **生成并配置管理员密钥**
   ```bash
   python generate_admin_key.py
   # 添加到 .env
   ```

3. **重启服务**
   ```bash
   docker-compose restart
   ```

4. **更新所有管理脚本**
   - 添加 `X-Admin-Key` header
   - 测试所有管理操作

5. **通知团队**
   - 分发新的管理员密钥
   - 更新文档和工具

## 参考资料

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Python secrets 模块](https://docs.python.org/3/library/secrets.html)

---

**更新时间**: 2025-01-02
**版本**: 1.0
