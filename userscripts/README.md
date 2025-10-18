# CSDN Helper - 油猴脚本 v2.0

> 一键解锁 CSDN VIP 文章和文库文档，获取资源下载直链

## ✨ 特性

- 🔓 **一键解锁 VIP 文章** - 无需VIP会员即可阅读付费文章
- 📚 **解锁文库文档** - 支持 CSDN 文库文档解锁
- ⚡ **超快响应** - 采用同步接口，无需等待，即点即得
- 🎨 **精美界面** - 内嵌预览窗口，支持新标签打开
- 📊 **实时日志** - 右下角日志面板，实时显示处理状态
- 🔗 **资源直链** - 获取 CSDN 资源真实下载链接

## 📦 安装

### 1. 安装 Tampermonkey

首先需要安装 Tampermonkey 浏览器扩展：

- [Chrome / Edge](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
- [Firefox](https://addons.mozilla.org/firefox/addon/tampermonkey/)
- [Safari](https://apps.apple.com/app/tampermonkey/id1482490089)

### 2. 安装脚本

1. 打开 `csdn_helper.js` 文件
2. 复制全部内容
3. 打开 Tampermonkey 管理面板
4. 点击"+"号创建新脚本
5. 粘贴代码并保存

或者直接点击文件，Tampermonkey 会自动识别并安装。

## ⚙️ 配置

### 修改服务器地址

编辑脚本开头的配置：

```javascript
const CONFIG = {
    // 修改为你的服务器地址（重要！）
    apiBaseUrl: 'http://175.24.164.85/api',  // 改成你的服务器IP或域名

    // 请求超时时间（毫秒）
    requestTimeout: 60000,

    // 是否显示日志面板（右下角）
    enableLog: true,

    // 是否优先内嵌预览（false则新标签打开）
    preferPreview: true,
};
```

### 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `apiBaseUrl` | API 服务器地址，修改为你部署的服务器地址 | `http://175.24.164.85/api` |
| `requestTimeout` | 请求超时时间（毫秒） | `60000` (60秒) |
| `enableLog` | 是否显示右下角日志面板 | `true` |
| `preferPreview` | 是否优先使用内嵌预览（false 则新标签打开） | `true` |

## 🚀 使用方法

### 解锁 VIP 文章

1. 打开任意 CSDN VIP 文章页面
2. 页面上方会出现 **🔓 一键解锁** 按钮
3. 点击按钮，等待几秒
4. 文章内容会在弹窗中显示
5. 可以选择"新标签打开"或直接阅读

### 解锁文库文档

1. 打开 CSDN 文库文档页面（wenku.csdn.net）
2. 点击 **🔓 一键解锁** 按钮
3. 文档内容会自动显示

### 获取资源直链

1. 打开 CSDN 资源下载页面（download.csdn.net）
2. 点击 **🔗 获取直链** 按钮
3. 自动打开真实下载链接

## 📋 支持的页面

- ✅ `https://blog.csdn.net/*/article/details/*` - CSDN 博客文章
- ✅ `https://wenku.csdn.net/answer/*` - CSDN 文库文档
- ✅ `https://download.csdn.net/download/*/*` - CSDN 资源下载

## 🎯 界面说明

### 解锁按钮

![解锁按钮](https://via.placeholder.com/400x60/667eea/ffffff?text=🔓+一键解锁)

- 出现在VIP文章顶部
- 鼠标悬停有动画效果
- 点击后显示"⏳ 解锁中..."
- 完成后显示"✅ 解锁成功"

### 日志面板

位于右下角的半透明黑色面板，显示：
- ℹ️ 信息日志（蓝色背景）
- ✅ 成功日志（绿色背景）
- ⚠️ 警告日志（黄色背景）
- ❌ 错误日志（红色背景）

### 预览窗口

全屏覆盖层，包含：
- 标题栏：显示"🎉 解锁成功"
- 操作按钮："新标签打开" 和 "关闭"
- 内容区域：iframe显示文章HTML

## 🔧 技术细节

### API 接口

#### 文章下载（同步）

```javascript
POST /api/article/download
Content-Type: application/json

Request:
{
    "url": "https://blog.csdn.net/xxx/article/details/123456"
}

Response:
{
    "success": true,
    "content": "<!DOCTYPE html>...",
    "file_size": 45678,
    "title": "文章标题",
    "error": null
}
```

#### 资源下载链接

```javascript
POST /api/file/get-download-link
Content-Type: application/json

Request:
{
    "url": "https://download.csdn.net/download/user/12345"
}

Response:
{
    "success": true,
    "download_url": "https://...",
    "source_id": "12345",
    "error": null,
    "message": "成功获取下载链接"
}
```

### 权限说明

脚本请求的权限：
- `GM_xmlhttpRequest` - 用于跨域 API 请求

### 连接域名

- `175.24.164.85` - 默认API服务器（修改为你的服务器）

## ❓ 常见问题

### Q: 点击按钮没有反应？

A: 检查以下几点：
1. Tampermonkey 是否启用
2. 脚本中的 `apiBaseUrl` 是否配置正确
3. 服务器是否正常运行
4. 打开浏览器控制台查看错误日志

### Q: 提示"网络请求失败"？

A: 可能的原因：
1. 服务器地址配置错误
2. 服务器未启动或无法访问
3. 防火墙阻止了请求
4. CORS 跨域问题（服务器需配置）

### Q: 解锁速度慢？

A:
1. 检查网络连接
2. 服务器性能可能不足
3. 增加 `requestTimeout` 超时时间

### Q: 如何关闭日志面板？

A: 修改配置：
```javascript
enableLog: false  // 不显示日志面板
```

### Q: 想要新标签打开而不是内嵌预览？

A: 修改配置：
```javascript
preferPreview: false  // 新标签打开
```

## 📝 更新日志

查看 [CHANGELOG.md](./CHANGELOG.md) 了解版本更新历史。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

MIT License

## ⚠️ 免责声明

本脚本仅供学习和研究使用，请勿用于商业用途。

使用本脚本获取的内容版权归原作者所有，请尊重原创，支持正版。

---

**Enjoy! 🎉**
