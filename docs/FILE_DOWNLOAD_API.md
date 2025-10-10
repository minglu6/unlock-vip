# CSDN资源下载API文档

## 📋 API概览

文件下载服务提供统一的接口获取CSDN资源的实际下载链接。

### 基础信息
- **Base URL**: `http://127.0.0.1:8000/api/file`
- **认证方式**: API Key（Header: `X-API-Key`）
- **默认测试Key**: `test-key-123`

---

## 🔗 API端点

### 1. 获取下载链接

**端点**: `POST /get-download-link`

**功能**: 通过CSDN资源下载页面URL获取真实下载链接

#### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| url | string | 是 | CSDN资源下载页面URL | `https://download.csdn.net/download/xxx/91316313` |

#### 请求示例

```json
{
    "url": "https://download.csdn.net/download/weixin_41645323/91316313"
}
```

#### 响应格式

**成功响应** (200 OK)
```json
{
    "success": true,
    "source_id": "91316313",
    "download_url": "https://dl-download.csdn.net/down11/20250709/...",
    "error": null,
    "message": "成功获取下载链接"
}
```

**失败响应** (200 OK - 业务失败)
```json
{
    "success": false,
    "source_id": "91316313",
    "download_url": null,
    "error": "请登录后操作",
    "message": "获取下载链接失败"
}
```

**错误响应** (400/500)
```json
{
    "detail": "必须提供url或source_id其中之一"
}
```

---

### 2. 健康检查

**端点**: `GET /health`

**功能**: 检查文件下载服务状态

#### 请求示例
```bash
curl -X GET "http://127.0.0.1:8000/api/file/health" \
  -H "X-API-Key: test-key-123"
```

#### 响应示例
```json
{
    "status": "healthy",
    "service": "file_download",
    "cookies_available": true,
    "api_endpoint": "https://download.csdn.net/api/source/detail/v1/download"
}
```

---

## 💻 使用示例

### cURL示例

**获取下载链接**
```bash
curl -X POST "http://127.0.0.1:8000/api/file/get-download-link" \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://download.csdn.net/download/weixin_41645323/91316313"}'
```

### PowerShell示例

**获取下载链接**
```powershell
$body = @{
    url = "https://download.csdn.net/download/weixin_41645323/91316313"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/file/get-download-link" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"; "X-API-Key"="test-key-123"} `
    -Body $body
```

### Python示例

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/file/get-download-link",
    headers={
        "X-API-Key": "test-key-123",
        "Content-Type": "application/json"
    },
    json={
        "url": "https://download.csdn.net/download/weixin_41645323/91316313"
    }
)

result = response.json()
if result["success"]:
    print(f"下载链接: {result['download_url']}")
else:
    print(f"失败: {result['error']}")
```

---

## 🔐 认证说明

所有API请求都需要在Header中提供有效的API Key：

```
X-API-Key: your-api-key-here
```

### 获取API Key

运行脚本生成测试密钥：
```bash
python scripts/generate_test_key.py
```

或查看现有密钥：
```bash
python scripts/list_api_keys.py
```

---

## ⚠️ 注意事项

### Cookie配置

1. **必需文件**: 项目根目录需要有 `cookies.json` 文件
2. **获取方式**: 从浏览器导出CSDN登录状态的cookies
3. **格式要求**: 标准的Netscape cookies格式或JSON数组

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `请登录后操作` | Cookie已过期 | 重新导出cookies.json |
| `无法从URL中提取资源ID` | URL格式不正确 | 检查URL格式，应为 `https://download.csdn.net/download/xxx/数字ID` |
| `401 Unauthorized` | API Key无效 | 检查X-API-Key header |

### 性能建议

- Cookie有效期通常为7-30天，建议定期更新
- 避免高频请求，建议添加适当的延迟（100-500ms）

---

## 📊 响应状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功（需检查响应中的success字段） |
| 400 | 请求参数错误 |
| 401 | 未授权（API Key无效） |
| 500 | 服务器内部错误 |

---

## 🔄 API版本

- **当前版本**: v1.0.0
- **最后更新**: 2025-10-03
- **变更日志**:
  - v1.0.0: 统一URL和ID接口，简化API设计

---

## 📦 Postman Collection

项目提供了完整的Postman测试集合：
- **文件位置**: `docs/POSTMAN_COLLECTION.json`
- **导入方式**: Postman → Import → 选择该文件
- **包含内容**: 所有API端点 + 预配置认证

---

## 🛠️ 技术细节

### URL格式支持

支持以下CSDN资源URL格式：
- `https://download.csdn.net/download/username/12345`
- `http://download.csdn.net/download/username/12345`

### 提取逻辑

从URL中提取最后一个斜杠后的数字作为资源ID：
```
https://download.csdn.net/download/weixin_41645323/91316313
                                                      ^^^^^^^^
                                                    source_id
```

### CSDN API调用

内部调用CSDN官方API：
```
POST https://download.csdn.net/api/source/detail/v1/download
Body: {"sourceId": 91316313}
```

---

## 📞 支持与反馈

如遇到问题或有改进建议，请：
1. 查看项目文档：`docs/README.md`
2. 查看快速开始：`QUICK_START.md`
3. 提交Issue或Pull Request
