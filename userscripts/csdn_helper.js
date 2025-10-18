// ==UserScript==
// @name         CSDN Helper
// @namespace    https://github.com/minglu6/unlock-vip
// @version      1.0.0
// @description  CSDN 全能助手 - 支持VIP文章/文库解锁、资源下载直链获取
// @author       minglu6
// @match        https://blog.csdn.net/*/article/details/*
// @match        https://*.blog.csdn.net/article/details/*
// @match        https://wenku.csdn.net/answer/*
// @match        https://download.csdn.net/download/*/*
// @grant        GM_xmlhttpRequest
// @icon         https://g.csdnimg.cn/static/logo/favicon32.ico
// @connect      175.24.164.85
// @license      MIT
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    const CONFIG = {
        apiBaseUrl: 'http://175.24.164.85/api',
        requestTimeout: 60000,
        enableLog: false,
        preferPreview: true,
    };

    class APIClient {
        constructor(baseUrl) {
            this.baseUrl = baseUrl;
        }

        async request(endpoint, options = {}) {
            const url = `${this.baseUrl}${endpoint}`;
            const method = options.method || 'GET';
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };
            const data = options.body ? JSON.stringify(options.body) : undefined;

            console.log('[CSDN Helper API] 请求参数:', {
                method: method,
                url: url,
                headers: headers,
                data: data
            });

            return new Promise((resolve, reject) => {
                GM_xmlhttpRequest({
                    method: method,
                    url: url,
                    headers: headers,
                    data: data,
                    timeout: options.timeout || CONFIG.requestTimeout,
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

        async downloadArticle(url) {
            return await this.request('/article/download', {
                method: 'POST',
                body: { url },
                timeout: CONFIG.requestTimeout
            });
        }

        async getDownloadLink(url) {
            return await this.request('/file/get-download-link', {
                method: 'POST',
                body: { url }
            });
        }
    }

    class LogPanel {
        constructor() {
            this.panel = null;
            this.logList = null;
            if (CONFIG.enableLog) {
                this.init();
            }
        }

        init() {
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

    class ResultPanel {
        constructor() {
            this.overlay = null;
            this.iframe = null;
            this.init();
        }

        init() {
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
                this.iframe.srcdoc = content;
                this.overlay.style.display = 'flex';

                const blob = new Blob([content], { type: 'text/html' });
                const blobUrl = URL.createObjectURL(blob);
                this.openNewTabLink.href = blobUrl;
            } else {
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

    class UnlockController {
        constructor() {
            this.apiClient = new APIClient(CONFIG.apiBaseUrl);
            this.logger = new LogPanel();
            this.resultPanel = new ResultPanel();
        }

        async unlockArticle(url) {
            try {
                this.logger.log(`开始解锁: ${url}`, 'info');
                this.logger.log('正在下载文章...', 'info');

                const result = await this.apiClient.downloadArticle(url);

                if (result.success && result.content) {
                    this.logger.log(`解锁成功: ${result.title || '未知标题'}`, 'success');
                    this.logger.log(`文件大小: ${(result.file_size / 1024).toFixed(2)} KB`, 'info');
                    this.resultPanel.show(result.content, result.title);
                    return true;
                } else {
                    throw new Error(result.error || '下载失败');
                }
            } catch (error) {
                this.logger.log(`解锁失败: ${error.message}`, 'error');
                throw error;
            }
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

    class UIInjector {
        constructor(controller) {
            this.controller = controller;
        }

        injectArticleButton() {
            const url = window.location.href;

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

            this.insertButton(button, vipElement);
        }

        insertButton(button, vipElement) {
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

            if (vipElement.parentElement) {
                vipElement.parentElement.insertBefore(button, vipElement.nextSibling);
            } else {
                document.body.appendChild(button);
            }
        }

        injectDownloadButton() {
            if (document.getElementById('csdn-unlock-download-btn')) return;

            const downloadBtnContainer = document.querySelector('#downloadBtn');

            if (!downloadBtnContainer) {
                console.log('[CSDN Helper] 未找到 #downloadBtn，尝试其他选择器...');
                const selectors = [
                    '.download-btn',
                    '.dl_download_box',
                    '#download',
                    '.resource_download',
                    '.dl_download_link',
                    'main',
                    'body'
                ];

                let targetElement = null;
                for (const selector of selectors) {
                    targetElement = document.querySelector(selector);
                    if (targetElement) break;
                }

                if (!targetElement) {
                    console.log('[CSDN Helper] 未找到合适的插入位置，将创建固定按钮');
                    this.createFixedDownloadButton();
                    return;
                }

                this.createStandaloneButton(targetElement);
                return;
            }

            const button = document.createElement('button');
            button.id = 'csdn-unlock-download-btn';
            button.type = 'button';
            button.className = 'el-button relative el-button--success el-button--medium';
            button.style.cssText = `
                margin-left: 12px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                border-color: #667eea !important;
                transition: all 0.3s ease !important;
            `;

            const span = document.createElement('span');
            span.textContent = '🔗 获取直链';
            button.appendChild(span);

            button.onmouseover = () => {
                button.style.transform = 'translateY(-2px)';
                button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.6)';
            };
            button.onmouseout = () => {
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.4)';
            };

            button.onclick = async (e) => {
                e.preventDefault();
                e.stopPropagation();

                const url = window.location.href;
                const originalText = span.textContent;
                span.textContent = '⏳ 获取中...';
                button.disabled = true;

                try {
                    const downloadUrl = await this.controller.getDownloadLink(url);
                    window.open(downloadUrl, '_blank');
                    span.textContent = '✅ 已打开';
                } catch (error) {
                    alert(`获取失败：${error.message}`);
                    span.textContent = originalText;
                } finally {
                    setTimeout(() => {
                        span.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            };

            downloadBtnContainer.appendChild(button);
            console.log('[CSDN Helper] 下载按钮已注入到 #downloadBtn');
        }

        createStandaloneButton(targetElement) {
            const button = document.createElement('button');
            button.id = 'csdn-unlock-download-btn';
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
                margin: 10px !important;
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

            if (targetElement.tagName === 'BODY' || targetElement.tagName === 'MAIN') {
                targetElement.insertBefore(button, targetElement.firstChild);
            } else {
                targetElement.parentElement.insertBefore(button, targetElement.nextSibling);
            }

            console.log('[CSDN Helper] 独立下载按钮已注入');
        }

        createFixedDownloadButton() {
            const button = document.createElement('button');
            button.id = 'csdn-unlock-download-btn';
            button.textContent = '🔗 获取直链';
            button.style.cssText = `
                position: fixed !important;
                top: 100px !important;
                right: 20px !important;
                padding: 12px 24px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: #fff !important;
                border: none !important;
                border-radius: 8px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5) !important;
                z-index: 2147483646 !important;
                transition: all 0.3s ease !important;
            `;

            button.onmouseover = () => {
                button.style.transform = 'translateY(-2px) scale(1.05)';
                button.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.7)';
            };
            button.onmouseout = () => {
                button.style.transform = 'translateY(0) scale(1)';
                button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.5)';
            };

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

            document.body.appendChild(button);
            console.log('[CSDN Helper] 固定下载按钮已创建');
        }
    }

    function init() {
        console.log('[CSDN Helper] 初始化中...');

        const controller = new UnlockController();
        const injector = new UIInjector(controller);

        const hostname = window.location.hostname;

        function tryInject(retryCount = 0) {
            if (hostname.includes('blog.csdn.net') || hostname.includes('wenku.csdn.net')) {
                injector.injectArticleButton();
            } else if (hostname.includes('download.csdn.net')) {
                injector.injectDownloadButton();

                if (!document.getElementById('csdn-unlock-download-btn') && retryCount < 5) {
                    console.log(`[CSDN Helper] 按钮注入失败，${500}ms 后重试 (${retryCount + 1}/5)`);
                    setTimeout(() => tryInject(retryCount + 1), 500);
                }
            }
        }

        tryInject();
        console.log('[CSDN Helper] 初始化完成');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
