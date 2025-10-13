# CSDN Helper 油猴脚本

> 基于自托管API服务的CSDN全能助手

## 快速开始

### 1. 安装油猴扩展
- Chrome/Edge: [Tampermonkey](https://www.tampermonkey.net/)
- Firefox: [Tampermonkey](https://addons.mozilla.org/zh-CN/firefox/addon/tampermonkey/)

### 2. 安装脚本
1. 复制 `csdn_helper.js` 的全部内容
2. 打开油猴 → "添加新脚本"
3. 粘贴并保存

### 3. 配置API密钥
在浏览器控制台（F12）执行：
```javascript
GM_setValue('csdn_api_key', '你的API密钥')
```

## 功能特性

- ✅ **VIP文章解锁** - 一键解锁CSDN博客VIP文章
- ✅ **文库解锁** - 支持CSDN文库VIP文档
- ✅ **资源直链** - 获取CSDN资源下载直链
- ✅ **实时日志** - 右下角显示操作日志
- ✅ **内嵌预览** - 支持内嵌预览或新标签打开

## 使用方法

### 解锁VIP文章/文库
访问VIP内容页面，点击自动出现的 **"🔓 一键解锁"** 按钮

### 获取资源直链
访问资源下载页面，点击 **"🔗 获取直链"** 按钮

## 配置选项

编辑脚本中的 `CONFIG` 对象：

```javascript
const CONFIG = {
    apiBaseUrl: 'http://175.24.164.85/api',  // API服务器地址
    apiKey: GM_getValue('csdn_api_key', ''), // API密钥
    pollIntervalMs: 2000,      // 轮询间隔（毫秒）
    pollTimeoutMs: 180000,     // 超时时间（3分钟）
    enableLog: true,           // 显示日志面板
    preferPreview: true,       // 优先内嵌预览
};
```

## API接口

脚本调用以下API接口：

| 功能 | 接口 |
|------|------|
| 提交解锁任务 | `POST /api/article/submit` |
| 查询任务状态 | `GET /api/article/task/{task_id}/status` |
| 获取解锁内容 | `GET /api/article/task/{task_id}/result` |
| 获取下载直链 | `POST /api/file/get-download-link` |

所有请求需要在Header中携带：`X-API-Key: your_api_key`

## 匹配规则

脚本自动在以下页面生效：
- `https://blog.csdn.net/*/article/details/*`
- `https://*.blog.csdn.net/article/details/*`
- `https://wenku.csdn.net/answer/*`
- `https://download.csdn.net/download/*/*`

## 技术架构

```
浏览器油猴脚本 (GM_xmlhttpRequest)
         ↓
   FastAPI服务器
         ↓
    Celery + Redis
```

## 常见问题

**Q: 提示未配置API密钥？**
A: 按照步骤3配置API密钥

**Q: 点击按钮无响应？**
A: 检查F12控制台错误，确认服务器可访问

**Q: 任务处理超时？**
A: 增加 `pollTimeoutMs` 配置值，或稍后重试

**Q: 想关闭日志面板？**
A: 设置 `enableLog: false`

## 完整文档

详细使用说明请查看：[USERSCRIPT_GUIDE.md](USERSCRIPT_GUIDE.md)

## 项目地址

https://github.com/minglu6/unlock-vip

## 许可证

MIT License
