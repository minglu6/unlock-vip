# 异步API使用示例

## 接口说明

现在只支持异步接口，以提高并发性能：

1. `POST /api/article/submit` - 提交下载任务
2. `GET /api/article/task/{task_id}/status` - 查询任务状态
3. `GET /api/article/task/{task_id}/result` - 获取任务结果（HTML内容）

## 使用流程

### 1. 提交任务

```bash
curl -X POST "http://localhost:8000/api/article/submit" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://blog.csdn.net/username/article/details/123456789"
  }'
```

返回示例：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "message": "任务已成功提交，请使用任务ID轮询状态"
}
```

### 2. 轮询任务状态

```bash
curl "http://localhost:8000/api/article/task/550e8400-e29b-41d4-a716-446655440000/status" \
  -H "X-API-Key: your_api_key"
```

返回示例：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING",
  "progress": 50,
  "result": null,
  "error": null
}
```

状态说明：
- `PENDING`: 任务等待中
- `PROCESSING`: 任务处理中
- `SUCCESS`: 任务成功
- `FAILURE`: 任务失败

### 3. 获取任务结果

当状态为 `SUCCESS` 时，可以获取HTML内容：

```bash
curl "http://localhost:8000/api/article/task/550e8400-e29b-41d4-a716-446655440000/result" \
  -H "X-API-Key: your_api_key"
```

返回示例：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "content": "<!DOCTYPE html>...",
  "file_size": 12345,
  "title": "文章标题",
  "error": null
}
```

## Python使用示例

```python
import requests
import time

def download_article_async(api_key, article_url):
    base_url = "http://localhost:8000"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # 1. 提交任务
    submit_data = {"url": article_url}
    response = requests.post(f"{base_url}/api/article/submit",
                           headers=headers, json=submit_data)

    if response.status_code != 200:
        raise Exception(f"任务提交失败: {response.text}")

    result = response.json()
    task_id = result["task_id"]
    print(f"任务提交成功，任务ID: {task_id}")

    # 2. 轮询状态
    while True:
        response = requests.get(f"{base_url}/api/article/task/{task_id}/status",
                              headers=headers)
        status_data = response.json()
        status = status_data["status"]

        print(f"任务状态: {status}")

        if status == "SUCCESS":
            break
        elif status == "FAILURE":
            raise Exception(f"任务失败: {status_data.get('error')}")

        time.sleep(1)  # 等待1秒

    # 3. 获取结果
    response = requests.get(f"{base_url}/api/article/task/{task_id}/result",
                          headers=headers)
    result_data = response.json()

    if result_data["success"]:
        html_content = result_data["content"]
        title = result_data["title"]
        print(f"下载成功: {title}")
        return html_content
    else:
        raise Exception(f"下载失败: {result_data.get('error')}")

# 使用示例
api_key = "your_api_key"
article_url = "https://blog.csdn.net/username/article/details/123456789"

try:
    html_content = download_article_async(api_key, article_url)
    # 处理HTML内容...
    print(f"获取到HTML内容，长度: {len(html_content)} 字符")
except Exception as e:
    print(f"错误: {str(e)}")
```

## 优势

1. **更好的用户体验**: 客户端可以快速得到响应，不需要长时间等待
2. **更高的并发处理**: 服务器可以处理更多并发请求
3. **任务可追踪**: 每个任务都有唯一的UUID，方便追踪和管理
4. **结果缓存**: 成功的任务结果会缓存1小时，可以重复获取
5. **纯异步处理**: 只支持异步接口，确保最佳并发性能

## 注意事项

1. 任务结果会在Redis中缓存1小时，之后会自动删除
2. 建议使用适当的轮询间隔（如1-2秒），避免过于频繁的请求
3. 如果任务失败，会返回详细的错误信息
4. 任务ID是UUID格式，确保全局唯一性