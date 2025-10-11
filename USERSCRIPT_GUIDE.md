# CSDN Helper 油猴脚本使用指南

## 功能介绍

基于自托管API服务的CSDN内容解锁工具，支持：
- ✅ CSDN博客VIP文章解锁
- ✅ CSDN文库VIP文档解锁
- ✅ CSDN资源下载直链获取
- ✅ 实时日志显示
- ✅ 内嵌预览/新标签打开

## 安装步骤

### 1. 安装油猴扩展

首先需要在浏览器中安装油猴（Tampermonkey）扩展：

- **Chrome/Edge**: [Tampermonkey官网](https://www.tampermonkey.net/)
- **Firefox**: [Tampermonkey附加组件](https://addons.mozilla.org/zh-CN/firefox/addon/tampermonkey/)

### 2. 安装脚本

1. 打开 `csdn_helper.js` 文件
2. 复制全部内容
3. 点击油猴图标 → "添加新脚本"
4. 粘贴代码并保存（Ctrl+S）

### 3. 配置API密钥

有三种方式配置API密钥：

#### 方式一：首次使用弹窗配置（推荐⭐）

1. 首次访问CSDN页面时，会自动弹出精美的密钥配置对话框
2. 在输入框中输入您的API密钥
3. 点击"确定"按钮保存（或按回车键）
4. 页面自动刷新后即可使用

**特点**：
- ✅ 最简单直观的配置方式
- ✅ 自动保存到浏览器本地存储
- ✅ 支持回车键快捷提交
- ✅ 精美的UI设计

#### 方式二：通过浏览器控制台

1. 在任意CSDN页面按 `F12` 打开开发者工具
2. 切换到 "Console（控制台）" 标签
3. 输入以下命令并回车：

```javascript
GM_setValue('csdn_api_key', '你的API密钥')
```

4. 刷新页面即可生效

#### 方式三：直接修改脚本

编辑脚本，找到配置部分：

```javascript
const CONFIG = {
    apiBaseUrl: 'http://175.24.164.85/api',
    apiKey: GM_getValue('csdn_api_key', ''),  // 在这里直接填写你的密钥
    // ...
};
```

将 `''` 改为 `'你的API密钥'`

### 4. 获取API密钥

联系管理员获取API密钥，或者如果你是项目部署者，可以通过以下方式创建：

```bash
# 在服务器上执行
curl -X POST "http://175.24.164.85/api/admin/api-keys" \
  -H "Content-Type: application/json" \
  -d '{"name": "我的密钥", "description": "用于油猴脚本"}'
```

## 使用方法

### 解锁博客文章

1. 访问任意CSDN VIP博客文章页面
2. 页面顶部会自动出现 **"🔓 一键解锁"** 按钮
3. 点击按钮，等待解锁完成
4. 解锁成功后会在弹出窗口显示完整内容

### 解锁文库文档

1. 访问CSDN文库VIP文档页面
2. 同样会出现 **"🔓 一键解锁"** 按钮
3. 点击解锁即可查看完整内容

### 获取资源下载直链

1. 访问CSDN资源下载页面
2. 页面会出现 **"🔗 获取直链"** 按钮
3. 点击后自动在新标签打开下载链接

### 查看日志

脚本运行时会在页面右下角显示日志面板：
- 蓝色 ℹ️：信息日志
- 绿色 ✅：成功日志
- 黄色 ⚠️：警告日志
- 红色 ❌：错误日志

点击"清空"按钮可清除日志历史。

## 配置说明

编辑脚本中的 `CONFIG` 对象可自定义行为：

```javascript
const CONFIG = {
    // API服务器地址（如果你有自己的服务器，修改这里）
    apiBaseUrl: 'http://175.24.164.85/api',

    // API密钥
    apiKey: GM_getValue('csdn_api_key', ''),

    // 轮询间隔（毫秒），越小响应越快但消耗越大
    pollIntervalMs: 2000,

    // 轮询超时（毫秒），超过这个时间会提示超时
    pollTimeoutMs: 180000,  // 3分钟

    // 是否显示日志面板
    enableLog: true,

    // 优先内嵌预览（false则直接新标签打开）
    preferPreview: true,
};
```

## 常见问题

### Q1: 提示"未配置API密钥"

**解决方案**：按照 [配置API密钥](#3-配置api密钥) 部分的说明配置密钥

### Q2: 点击按钮没有反应

**检查步骤**：
1. 按 F12 打开开发者工具，查看Console是否有错误
2. 确认API服务器是否正常运行
3. 检查网络是否能访问 `http://175.24.164.85`

### Q3: 提示"任务处理超时"

**可能原因**：
- 服务器负载过高
- 网络连接不稳定
- 文章内容过长

**解决方案**：稍后重试，或增加 `pollTimeoutMs` 配置值

### Q4: 解锁后内容显示异常

**解决方案**：
- 点击"新标签打开"按钮在新窗口查看
- 或设置 `preferPreview: false` 默认使用新标签打开

### Q5: 想要关闭日志面板

修改配置：
```javascript
enableLog: false,
```

## 技术架构

```
┌─────────────────┐
│  油猴脚本        │
│  (浏览器前端)    │
└────────┬────────┘
         │ GM_xmlhttpRequest
         │
┌────────▼────────┐
│  FastAPI服务    │
│  (175.24.164.85)│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│Celery│  │Redis │
│异步队列│  │缓存  │
└──────┘  └──────┘
```

## API接口说明

脚本使用以下API接口：

### 文章解锁API

- **提交任务**: `POST /api/article/submit`
- **查询状态**: `GET /api/article/task/{task_id}/status`
- **获取结果**: `GET /api/article/task/{task_id}/result`

### 文件下载API

- **获取直链**: `POST /api/file/get-download-link`

所有请求需要在Header中携带：
```
X-API-Key: your_api_key
```

## 更新日志

### v2.1.0 (2025-01-10)
- 🎉 新增API密钥配置弹窗
- ✨ 首次使用自动显示配置对话框
- 🎨 精美的密钥输入UI设计
- ⌨️ 支持回车键快捷提交
- 🔄 配置完成自动刷新页面

### v2.0.0 (2025-01-10)
- 🎉 首次发布
- ✅ 支持博客文章解锁
- ✅ 支持文库文档解锁
- ✅ 支持资源下载直链
- ✅ 实时日志面板
- ✅ 内嵌预览功能

## 许可证

MIT License

## 支持

如有问题，请提交Issue或联系维护者。

项目地址：https://github.com/minglu6/unlock-vip
