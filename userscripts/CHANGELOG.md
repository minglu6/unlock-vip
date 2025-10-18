# CSDN Helper 更新日志

## v2.0.0 - 2025-01-XX（当前版本）

### 重大更新

- 🚀 **改用同步接口**：移除异步任务队列机制，直接返回结果，响应更快
- ⚡ **简化架构**：移除 API 密钥验证，无需配置即可使用
- 🎯 **优化体验**：减少轮询等待时间，一键解锁即刻完成

### 变更内容

#### API 接口变更
- **移除**：
  - `POST /api/article/submit` - 提交任务接口
  - `GET /api/article/task/{task_id}/status` - 查询任务状态接口
  - `GET /api/article/task/{task_id}/result` - 获取任务结果接口

- **新增**：
  - `POST /api/article/download` - 同步下载接口（直接返回 HTML）

#### 代码变更
- 简化 `APIClient` 类，移除任务相关方法
- 移除 `pollTaskStatus` 轮询逻辑
- 移除 `ApiKeyDialog` 配置对话框（保留代码但不使用）
- 简化 `unlockArticle` 方法，直接调用同步接口
- 移除 `GM_setValue` 和 `GM_getValue` 权限

#### 配置变更
- 移除 `pollIntervalMs`（轮询间隔）配置
- 移除 `pollTimeoutMs`（轮询超时）配置
- 移除 `apiKey`（API 密钥）配置
- 新增 `requestTimeout`（请求超时）配置

### 响应格式

#### 旧版本（v1.x）
```javascript
// 需要三步：提交 → 轮询 → 获取结果
1. POST /api/article/submit
   Response: { task_id, status, message }

2. GET /api/article/task/{task_id}/status (轮询)
   Response: { task_id, status, progress, result, error }

3. GET /api/article/task/{task_id}/result
   Response: { task_id, success, content, file_size, title, error }
```

#### 新版本（v2.0）
```javascript
// 一步完成：直接获取结果
POST /api/article/download
Request: { url }
Response: { success, content, file_size, title, error }
```

### 使用方法

#### 安装
1. 在浏览器中安装 [Tampermonkey](https://www.tampermonkey.net/) 扩展
2. 打开 `csdn_helper.js` 文件
3. 点击"安装"按钮

#### 配置
修改脚本开头的 `CONFIG` 对象：

```javascript
const CONFIG = {
    // 修改为你的服务器地址
    apiBaseUrl: 'http://your-server-ip/api',

    // 请求超时时间（毫秒）
    requestTimeout: 60000,

    // 是否显示日志面板
    enableLog: true,

    // 是否优先内嵌预览
    preferPreview: true,
};
```

### 兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

### 已知问题

无

---

## v1.0.0 - 2024-XX-XX

### 初始版本

- ✨ 支持 VIP 文章解锁
- ✨ 支持文库文档解锁
- ✨ 支持资源下载直链获取
- ✨ 异步任务队列处理
- ✨ API 密钥验证
- ✨ 日志面板显示
- ✨ 结果预览面板
