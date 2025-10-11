// ==UserScript==
// @name         CSDN Helper
// @namespace    https://github.com/minglu6/unlock-vip
// @version      1.0.0
// @description  CSDN 全能助手 - 支持VIP文章/文库解锁、资源下载直链获取，基于自托管API服务
// @author       minglu6
// @match        https://blog.csdn.net/*/article/details/*
// @match        https://*.blog.csdn.net/article/details/*
// @match        https://wenku.csdn.net/answer/*
// @match        https://download.csdn.net/download/*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @icon         https://g.csdnimg.cn/static/logo/favicon32.ico
// @connect      175.24.164.85
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    // ========== 配置 ==========
    const CONFIG = {
        // API服务器地址
        apiBaseUrl: 'http://175.24.164.85/api',

        // API密钥（请在浏览器控制台执行：GM_setValue('csdn_api_key', '你的密钥')）
        // 或者直接在这里填写
        apiKey: GM_getValue('csdn_api_key', ''),

        // 轮询配置
        pollIntervalMs: 2000,      // 轮询间隔（毫秒）
        pollTimeoutMs: 180000,     // 轮询超时（3分钟）

        // 显示配置
        enableLog: true,           // 是否显示日志面板
        preferPreview: true,       // 优先内嵌预览（false则新标签打开）
    };

    // ========== API客户端 ==========
    class APIClient {
        constructor(baseUrl, apiKey) {
            this.baseUrl = baseUrl;
            this.apiKey = apiKey;
        }

        async request(endpoint, options = {}) {
            const url = `${this.baseUrl}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey,
                ...options.headers
            };

            return new Promise((resolve, reject) => {
                GM_xmlhttpRequest({
                    method: options.method || 'GET',
                    url: url,
                    headers: headers,
                    data: options.body ? JSON.stringify(options.body) : undefined,
                    timeout: options.timeout || 30000,
                    onload: (response) => {
                        try {
                            if (response.status >= 200 && response.status < 300) {
                                const data = JSON.parse(response.responseText);
                                resolve(data);
                            } else {
                                const error = JSON.parse(response.responseText || '{}');
                                reject(new Error(error.detail || `请求失败 (${response.status})`));
                            }
                        } catch (e) {
                            reject(new Error(`解析响应失败: ${e.message}`));
                        }
                    },
                    onerror: () => reject(new Error('网络请求失败')),
                    ontimeout: () => reject(new Error('请求超时'))
                });
            });
        }

        // 提交文章下载任务
        async submitArticleTask(url) {
            return await this.request('/article/submit', {
                method: 'POST',
                body: { url }
            });
        }

        // 查询任务状态
        async getTaskStatus(taskId) {
            return await this.request(`/article/task/${taskId}/status`);
        }

        // 获取任务结果
        async getTaskResult(taskId) {
            return await this.request(`/article/task/${taskId}/result`);
        }

        // 获取文件下载链接
        async getDownloadLink(url) {
            return await this.request('/file/get-download-link', {
                method: 'POST',
                body: { url }
            });
        }
    }

    // ========== 日志面板 ==========
    class LogPanel {
        constructor() {
            this.panel = null;
            this.logList = null;
            if (CONFIG.enableLog) {
                this.init();
            }
        }

        init() {
            // 创建面板容器
            this.panel = document.createElement('div');
            this.panel.id = 'csdn-unlock-log-panel';
            this.panel.style.cssText = `
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                width: 400px !important;
                max-height: 500px !important;
                background: rgba(0, 0, 0, 0.92) !important;
                color: #fff !important;
                font-size: 13px !important;
                border-radius: 10px !important;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
                z-index: 2147483647 !important;
                overflow: hidden !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
            `;

            // 标题栏
            const header = document.createElement('div');
            header.style.cssText = `
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                padding: 12px 16px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                border-bottom: 1px solid rgba(255,255,255,0.1) !important;
            `;

            const title = document.createElement('span');
            title.textContent = '🔓 CSDN 解锁日志';
            title.style.fontWeight = 'bold';

            const clearBtn = document.createElement('button');
            clearBtn.textContent = '清空';
            clearBtn.style.cssText = `
                background: rgba(255,255,255,0.2) !important;
                border: none !important;
                color: #fff !important;
                padding: 4px 12px !important;
                border-radius: 5px !important;
                cursor: pointer !important;
                font-size: 12px !important;
            `;
            clearBtn.onmouseover = () => clearBtn.style.background = 'rgba(255,255,255,0.3)';
            clearBtn.onmouseout = () => clearBtn.style.background = 'rgba(255,255,255,0.2)';
            clearBtn.onclick = () => this.clear();

            header.appendChild(title);
            header.appendChild(clearBtn);

            // 日志列表
            this.logList = document.createElement('div');
            this.logList.style.cssText = `
                padding: 12px !important;
                overflow-y: auto !important;
                max-height: 400px !important;
            `;

            this.panel.appendChild(header);
            this.panel.appendChild(this.logList);
            document.documentElement.appendChild(this.panel);
        }

        log(message, type = 'info') {
            if (!CONFIG.enableLog || !this.logList) return;

            const line = document.createElement('div');
            line.style.cssText = `
                padding: 6px 8px !important;
                margin-bottom: 4px !important;
                border-radius: 5px !important;
                font-size: 12px !important;
                line-height: 1.5 !important;
            `;

            const timestamp = new Date().toLocaleTimeString('zh-CN');
            const icon = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
            const color = type === 'error' ? 'rgba(239, 68, 68, 0.2)' :
                         type === 'success' ? 'rgba(34, 197, 94, 0.2)' :
                         type === 'warning' ? 'rgba(234, 179, 8, 0.2)' :
                         'rgba(59, 130, 246, 0.2)';

            line.style.background = color;
            line.innerHTML = `<span style="opacity: 0.7;">${timestamp}</span> ${icon} ${message}`;

            this.logList.appendChild(line);

            // 限制日志数量
            while (this.logList.childNodes.length > 100) {
                this.logList.removeChild(this.logList.firstChild);
            }

            this.logList.scrollTop = this.logList.scrollHeight;
        }

        clear() {
            if (this.logList) {
                this.logList.innerHTML = '';
            }
        }
    }

    // ========== API密钥配置面板 ==========
    class ApiKeyDialog {
        constructor() {
            this.overlay = null;
            this.init();
        }

        init() {
            // 创建遮罩层
            this.overlay = document.createElement('div');
            this.overlay.style.cssText = `
                position: fixed !important;
                inset: 0 !important;
                background: rgba(0, 0, 0, 0.85) !important;
                z-index: 2147483647 !important;
                display: none !important;
                align-items: center !important;
                justify-content: center !important;
                padding: 20px !important;
            `;

            // 对话框容器
            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: #1a1a1a !important;
                border-radius: 12px !important;
                box-shadow: 0 8px 40px rgba(0,0,0,0.5) !important;
                width: min(500px, 90vw) !important;
                overflow: hidden !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
            `;

            // 标题栏
            const header = document.createElement('div');
            header.style.cssText = `
                padding: 20px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: #fff !important;
                text-align: center !important;
            `;
            header.innerHTML = `
                <div style="font-size: 32px; margin-bottom: 8px;">🔑</div>
                <h2 style="margin: 0; font-size: 20px; font-weight: 600;">配置API密钥</h2>
            `;

            // 内容区域
            const content = document.createElement('div');
            content.style.cssText = `
                padding: 30px !important;
                color: #e0e0e0 !important;
            `;

            const description = document.createElement('p');
            description.style.cssText = `
                margin: 0 0 20px 0 !important;
                font-size: 14px !important;
                line-height: 1.6 !important;
                color: #b0b0b0 !important;
            `;
            description.textContent = '首次使用需要配置API密钥，请输入您的密钥以继续：';

            // 输入框
            const inputWrapper = document.createElement('div');
            inputWrapper.style.cssText = 'margin-bottom: 20px !important;';

            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = '请输入API密钥';
            input.style.cssText = `
                width: 100% !important;
                padding: 12px 16px !important;
                background: #2a2a2a !important;
                border: 2px solid #3a3a3a !important;
                border-radius: 8px !important;
                color: #fff !important;
                font-size: 14px !important;
                box-sizing: border-box !important;
                transition: border-color 0.3s ease !important;
            `;
            input.onfocus = () => input.style.borderColor = '#667eea';
            input.onblur = () => input.style.borderColor = '#3a3a3a';

            // 提示信息
            const hint = document.createElement('div');
            hint.style.cssText = `
                margin-top: 15px !important;
                padding: 12px !important;
                background: rgba(102, 126, 234, 0.1) !important;
                border-left: 3px solid #667eea !important;
                border-radius: 4px !important;
                font-size: 12px !important;
                line-height: 1.5 !important;
                color: #a0a0a0 !important;
            `;
            hint.innerHTML = `
                <strong style="color: #667eea;">💡 提示：</strong><br>
                • 密钥将安全保存在浏览器本地存储中<br>
                • 如需修改，可以在控制台执行：<br>
                <code style="background: #2a2a2a; padding: 2px 6px; border-radius: 3px; color: #8cc8ff;">GM_setValue('csdn_api_key', '新密钥')</code>
            `;

            inputWrapper.appendChild(input);
            content.appendChild(description);
            content.appendChild(inputWrapper);
            content.appendChild(hint);

            // 按钮区域
            const footer = document.createElement('div');
            footer.style.cssText = `
                padding: 0 30px 30px 30px !important;
                display: flex !important;
                gap: 12px !important;
            `;

            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = '取消';
            cancelBtn.style.cssText = `
                flex: 1 !important;
                padding: 12px !important;
                background: #3a3a3a !important;
                color: #e0e0e0 !important;
                border: none !important;
                border-radius: 8px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
            `;
            cancelBtn.onmouseover = () => cancelBtn.style.background = '#4a4a4a';
            cancelBtn.onmouseout = () => cancelBtn.style.background = '#3a3a3a';
            cancelBtn.onclick = () => this.hide();

            const confirmBtn = document.createElement('button');
            confirmBtn.textContent = '确定';
            confirmBtn.style.cssText = `
                flex: 2 !important;
                padding: 12px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: #fff !important;
                border: none !important;
                border-radius: 8px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
            `;
            confirmBtn.onmouseover = () => confirmBtn.style.transform = 'translateY(-2px)';
            confirmBtn.onmouseout = () => confirmBtn.style.transform = 'translateY(0)';

            // 确认按钮点击事件
            confirmBtn.onclick = () => {
                const apiKey = input.value.trim();
                if (!apiKey) {
                    alert('请输入API密钥！');
                    input.focus();
                    return;
                }
                this.saveApiKey(apiKey);
            };

            // 支持回车提交
            input.onkeypress = (e) => {
                if (e.key === 'Enter') {
                    confirmBtn.click();
                }
            };

            footer.appendChild(cancelBtn);
            footer.appendChild(confirmBtn);

            dialog.appendChild(header);
            dialog.appendChild(content);
            dialog.appendChild(footer);
            this.overlay.appendChild(dialog);
            document.documentElement.appendChild(this.overlay);

            this.input = input;
        }

        show() {
            this.overlay.style.display = 'flex';
            // 延迟聚焦，确保显示后再聚焦
            setTimeout(() => this.input.focus(), 100);
        }

        hide() {
            this.overlay.style.display = 'none';
            this.input.value = '';
        }

        saveApiKey(apiKey) {
            try {
                GM_setValue('csdn_api_key', apiKey);
                this.hide();

                // 显示成功提示
                alert('API密钥配置成功！\n页面将刷新以应用新配置。');

                // 刷新页面以应用新密钥
                window.location.reload();
            } catch (error) {
                alert(`保存失败：${error.message}`);
            }
        }
    }

    // ========== 结果展示面板 ==========
    class ResultPanel {
        constructor() {
            this.overlay = null;
            this.iframe = null;
            this.init();
        }

        init() {
            // 创建遮罩层
            this.overlay = document.createElement('div');
            this.overlay.style.cssText = `
                position: fixed !important;
                inset: 0 !important;
                background: rgba(0, 0, 0, 0.85) !important;
                z-index: 2147483646 !important;
                display: none !important;
                align-items: center !important;
                justify-content: center !important;
                padding: 40px !important;
            `;

            // 内容容器
            const container = document.createElement('div');
            container.style.cssText = `
                width: min(1200px, 95vw) !important;
                height: min(90vh, 1200px) !important;
                background: #0f0f0f !important;
                border-radius: 12px !important;
                overflow: hidden !important;
                display: flex !important;
                flex-direction: column !important;
                box-shadow: 0 8px 40px rgba(0,0,0,0.5) !important;
            `;

            // 标题栏
            const header = document.createElement('div');
            header.style.cssText = `
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                padding: 14px 20px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: #fff !important;
            `;

            const title = document.createElement('span');
            title.textContent = '🎉 解锁成功';
            title.style.cssText = 'font-weight: bold; font-size: 16px;';

            const actions = document.createElement('div');
            actions.style.cssText = 'display: flex; gap: 10px;';

            const openNewTab = document.createElement('a');
            openNewTab.textContent = '新标签打开';
            openNewTab.target = '_blank';
            openNewTab.style.cssText = `
                padding: 6px 14px !important;
                background: rgba(255,255,255,0.2) !important;
                color: #fff !important;
                text-decoration: none !important;
                border-radius: 6px !important;
                font-size: 13px !important;
            `;

            const closeBtn = document.createElement('button');
            closeBtn.textContent = '关闭';
            closeBtn.style.cssText = `
                padding: 6px 14px !important;
                background: rgba(255,255,255,0.2) !important;
                color: #fff !important;
                border: none !important;
                border-radius: 6px !important;
                cursor: pointer !important;
                font-size: 13px !important;
            `;
            closeBtn.onclick = () => this.hide();

            actions.appendChild(openNewTab);
            actions.appendChild(closeBtn);
            header.appendChild(title);
            header.appendChild(actions);

            // iframe容器
            this.iframe = document.createElement('iframe');
            this.iframe.style.cssText = `
                flex: 1 !important;
                border: none !important;
                background: #fff !important;
            `;
            this.iframe.setAttribute('sandbox', 'allow-same-origin allow-scripts allow-forms allow-modals');

            container.appendChild(header);
            container.appendChild(this.iframe);
            this.overlay.appendChild(container);
            document.documentElement.appendChild(this.overlay);

            this.openNewTabLink = openNewTab;
        }

        show(content, title = '解锁成功') {
            if (CONFIG.preferPreview) {
                // 内嵌预览
                this.iframe.srcdoc = content;
                this.overlay.style.display = 'flex';

                // 创建Blob URL用于新标签打开
                const blob = new Blob([content], { type: 'text/html' });
                const blobUrl = URL.createObjectURL(blob);
                this.openNewTabLink.href = blobUrl;
            } else {
                // 直接新标签打开
                const blob = new Blob([content], { type: 'text/html' });
                const blobUrl = URL.createObjectURL(blob);
                window.open(blobUrl, '_blank');
            }
        }

        hide() {
            this.overlay.style.display = 'none';
            this.iframe.srcdoc = '';
        }
    }

    // ========== 主控制器 ==========
    class UnlockController {
        constructor() {
            this.apiClient = new APIClient(CONFIG.apiBaseUrl, CONFIG.apiKey);
            this.logger = new LogPanel();
            this.resultPanel = new ResultPanel();
        }

        async unlockArticle(url) {
            try {
                this.logger.log(`开始解锁: ${url}`, 'info');

                // 1. 提交任务
                this.logger.log('正在提交任务...', 'info');
                const submitResult = await this.apiClient.submitArticleTask(url);
                const taskId = submitResult.task_id;
                this.logger.log(`任务已提交，ID: ${taskId}`, 'success');

                // 2. 轮询任务状态
                const result = await this.pollTaskStatus(taskId);

                // 3. 获取并显示结果
                this.logger.log('获取解锁内容...', 'info');
                const resultData = await this.apiClient.getTaskResult(taskId);

                if (resultData.success && resultData.content) {
                    this.logger.log(`解锁成功: ${resultData.title || '未知标题'}`, 'success');
                    this.resultPanel.show(resultData.content, resultData.title);
                    return true;
                } else {
                    throw new Error(resultData.error || '获取内容失败');
                }
            } catch (error) {
                this.logger.log(`解锁失败: ${error.message}`, 'error');
                throw error;
            }
        }

        async pollTaskStatus(taskId) {
            const startTime = Date.now();
            let lastProgress = 0;

            while (Date.now() - startTime < CONFIG.pollTimeoutMs) {
                try {
                    const status = await this.apiClient.getTaskStatus(taskId);

                    // 显示进度
                    if (status.progress && status.progress !== lastProgress) {
                        this.logger.log(`处理进度: ${status.progress}%`, 'info');
                        lastProgress = status.progress;
                    }

                    if (status.status === 'SUCCESS') {
                        return status.result;
                    } else if (status.status === 'FAILURE') {
                        throw new Error(status.error || '任务执行失败');
                    } else if (status.status === 'PROCESSING') {
                        this.logger.log('任务处理中...', 'info');
                    }

                    // 等待后继续轮询
                    await new Promise(resolve => setTimeout(resolve, CONFIG.pollIntervalMs));
                } catch (error) {
                    if (error.message.includes('任务执行失败')) {
                        throw error;
                    }
                    // 其他错误继续轮询
                    await new Promise(resolve => setTimeout(resolve, CONFIG.pollIntervalMs));
                }
            }

            throw new Error('任务处理超时，请稍后重试');
        }

        async getDownloadLink(url) {
            try {
                this.logger.log(`获取下载链接: ${url}`, 'info');
                const result = await this.apiClient.getDownloadLink(url);

                if (result.success && result.download_url) {
                    this.logger.log('获取下载链接成功', 'success');
                    return result.download_url;
                } else {
                    throw new Error(result.error || '获取下载链接失败');
                }
            } catch (error) {
                this.logger.log(`获取下载链接失败: ${error.message}`, 'error');
                throw error;
            }
        }
    }

    // ========== UI注入 ==========
    class UIInjector {
        constructor(controller) {
            this.controller = controller;
        }

        injectArticleButton() {
            const url = window.location.href;

            // 检测VIP元素
            const vipSelectors = [
                'a.article-vip-box[href="https://mall.csdn.net/vip"]',
                '#vip-info-wrap.vip-info-wrap',
                '.info-header-text'
            ];

            let vipElement = null;
            for (const selector of vipSelectors) {
                vipElement = document.querySelector(selector);
                if (vipElement) break;
            }

            if (!vipElement) {
                console.log('[CSDN Unlock] 未检测到VIP内容');
                return;
            }

            // 创建解锁按钮
            const button = document.createElement('button');
            button.textContent = '🔓 一键解锁';
            button.style.cssText = `
                padding: 8px 20px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: #fff !important;
                border: none !important;
                border-radius: 6px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                margin-left: 12px !important;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4) !important;
                transition: all 0.3s ease !important;
            `;

            button.onmouseover = () => {
                button.style.transform = 'translateY(-2px)';
                button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.6)';
            };
            button.onmouseout = () => {
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.4)';
            };

            let isProcessing = false;
            button.onclick = async () => {
                if (isProcessing) return;

                isProcessing = true;
                const originalText = button.textContent;
                button.textContent = '⏳ 解锁中...';
                button.disabled = true;
                button.style.opacity = '0.7';

                try {
                    await this.controller.unlockArticle(url);
                    button.textContent = '✅ 解锁成功';
                } catch (error) {
                    alert(`解锁失败：${error.message}`);
                    button.textContent = originalText;
                } finally {
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                        button.style.opacity = '1';
                        isProcessing = false;
                    }, 2000);
                }
            };

            // 插入按钮
            this.insertButton(button, vipElement);
        }

        insertButton(button, vipElement) {
            // 尝试多种插入位置
            const barContent = document.querySelector('.article-bar-top .bar-content');
            if (barContent) {
                barContent.appendChild(button);
                return;
            }

            const dataDiv = document.querySelector('.data');
            if (dataDiv) {
                dataDiv.appendChild(button);
                return;
            }

            // 兜底方案
            if (vipElement.parentElement) {
                vipElement.parentElement.insertBefore(button, vipElement.nextSibling);
            } else {
                document.body.appendChild(button);
            }
        }

        injectDownloadButton() {
            // 为CSDN下载页面注入获取直链按钮
            const downloadBtn = document.querySelector('.download-btn, .dl_download_box a');
            if (!downloadBtn) return;

            const button = document.createElement('button');
            button.textContent = '🔗 获取直链';
            button.style.cssText = `
                padding: 10px 24px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: #fff !important;
                border: none !important;
                border-radius: 6px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                margin-left: 15px !important;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4) !important;
            `;

            button.onclick = async () => {
                const url = window.location.href;
                const originalText = button.textContent;
                button.textContent = '⏳ 获取中...';
                button.disabled = true;

                try {
                    const downloadUrl = await this.controller.getDownloadLink(url);
                    window.open(downloadUrl, '_blank');
                    button.textContent = '✅ 已打开';
                } catch (error) {
                    alert(`获取失败：${error.message}`);
                    button.textContent = originalText;
                } finally {
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            };

            downloadBtn.parentElement.appendChild(button);
        }
    }

    // ========== 初始化 ==========
    function init() {
        // 检查API密钥
        if (!CONFIG.apiKey) {
            console.warn('[CSDN Helper] 未配置API密钥，显示配置对话框');

            // 显示密钥配置对话框
            const dialog = new ApiKeyDialog();
            dialog.show();
            return;
        }

        const controller = new UnlockController();
        const injector = new UIInjector(controller);

        const hostname = window.location.hostname;
        if (hostname.includes('blog.csdn.net') || hostname.includes('wenku.csdn.net')) {
            injector.injectArticleButton();
        } else if (hostname.includes('download.csdn.net')) {
            injector.injectDownloadButton();
        }
    }

    // 等待页面加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
