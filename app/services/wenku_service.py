"""
CSDN文库文档下载服务
专门处理wenku.csdn.net的文档下载和解锁
仅使用cookies.json进行身份验证，不包含自动登录功能
"""
import os
import re
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import markdown
from app.utils.cookie_parser import load_cookies

logger = logging.getLogger(__name__)

class WenkuService:
    """CSDN文库文档下载服务 - 基于cookies的简化版本"""

    def __init__(self, cookies_file: str = 'cookies.json'):
        """
        初始化文库服务

        Args:
            cookies_file: cookies文件路径，默认为 cookies.json
        """
        self.cookies_file = cookies_file
        self.session = None

    def _load_session(self):
        """从cookies文件加载session"""
        if self.session:
            return

        # 初始化session
        self.session = requests.Session()

        # 使用 cookie_parser 加载cookies（自动识别格式）
        try:
            cookies_dict = load_cookies(self.cookies_file)

            # 设置cookies到正确的域
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, str(value), domain='.csdn.net')

            # 设置请求头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            })

            logger.info("成功加载cookies并初始化session")

        except FileNotFoundError:
            logger.error(f"cookies文件不存在: {self.cookies_file}")
            raise Exception(f"cookies文件不存在: {self.cookies_file}，请先手动获取cookies")
        except Exception as e:
            logger.error(f"加载cookies失败: {str(e)}")
            raise Exception(f"加载cookies失败: {str(e)}")

    def extract_wenku_id(self, url: str) -> str:
        """
        从CSDN文库URL中提取文档ID

        Args:
            url: CSDN文库URL，如 https://wenku.csdn.net/answer/3pzv32zt84

        Returns:
            str: 文档ID
        """
        # 提取answer后面的ID
        match = re.search(r'wenku\.csdn\.net/(answer|doc|column)/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(2)

        # 尝试其他可能的URL格式
        match = re.search(r'wenku\.csdn\.net/[^/]+/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)

        raise Exception(f"无法从URL中提取CSDN文库文档ID: {url}")

    def is_vip_wenku_locked(self, html_content: str) -> bool:
        """
        检测CSDN文库文档是否为VIP锁定状态

        Args:
            html_content: 文档HTML内容

        Returns:
            bool: 是否为VIP锁定状态
        """
        # VIP锁定的关键标志
        vip_lock_indicators = [
            '阅读全文',
            'vip-mask',
            'vip-lock',
            'data-vip="true"',
            'class="open"',
            'open-btn',
            'text-all',
            '继续阅读',
            '付费阅读',
            '会员专享'
        ]

        content_lower = html_content.lower()

        for indicator in vip_lock_indicators:
            if indicator.lower() in content_lower:
                logger.info(f"检测到CSDN文库VIP锁定标志: {indicator}")
                return True

        return False

    def unlock_vip_wenku(self, wenku_id: str) -> bool:
        """
        解锁CSDN文库VIP文档

        Args:
            wenku_id: 文档ID

        Returns:
            bool: 是否解锁成功
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔓 开始解锁CSDN文库VIP文档")
        logger.info(f"{'='*60}")
        logger.info(f"📄 文档ID: {wenku_id}")

        try:
            # CSDN文库的解锁接口可能与博客不同，这里尝试几种可能的方式
            # 方式1: 尝试通用的VIP解锁接口
            unlock_urls = [
                "https://wenku.csdn.net/phoenix/web/v1/vip-article-read",
                "https://wenku.csdn.net/phoenix/web/v1/vip-wenku-read",
                "https://blog.csdn.net/phoenix/web/v1/vip-article-read"  # 回退到博客接口
            ]

            payload = {"articleId": wenku_id, "wenkuId": wenku_id}

            for unlock_url in unlock_urls:
                try:
                    logger.info(f"尝试解锁接口: {unlock_url}")
                    response = self.session.post(unlock_url, json=payload, timeout=30, verify=False)

                    logger.info(f"响应状态码: {response.status_code}")
                    logger.info(f"响应内容: {response.text[:500]}")

                    if response.status_code == 200:
                        try:
                            result = response.json()
                            logger.info(f"📨 API响应: {json.dumps(result, ensure_ascii=False)}")

                            if result.get('code') == 200:
                                logger.info(f"✅ CSDN文库VIP文档解锁成功！")
                                logger.info(f"{'='*60}\n")
                                return True
                            elif result.get('code') == 400:
                                logger.info(f"ℹ️  文档可能不是VIP文档或已解锁")
                                logger.info(f"{'='*60}\n")
                                return True
                            else:
                                logger.warning(f"⚠️  解锁失败: code={result.get('code')}, message={result.get('message')}")

                        except json.JSONDecodeError:
                            logger.warning(f"解锁API返回非JSON响应: {response.text[:100]}")

                except Exception as e:
                    logger.warning(f"解锁接口 {unlock_url} 失败: {str(e)}")
                    continue

            logger.info(f"{'='*60}\n")
            return False

        except Exception as e:
            logger.error(f"解锁CSDN文库VIP文档失败: {str(e)}")
            logger.info(f"{'='*60}\n")
            return False

    def download_wenku_document(self, url: str) -> dict:
        """
        下载CSDN文库文档

        Args:
            url: 文档URL

        Returns:
            dict: 包含url、title、html、content等信息的字典
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"📚 CSDN文库文档下载")
        logger.info(f"{'='*70}")
        logger.info(f"目标URL: {url}\n")

        # 加载session
        self._load_session()

        # 提取文档ID
        try:
            wenku_id = self.extract_wenku_id(url)
            logger.info(f"✅ 提取到文档ID: {wenku_id}")
        except Exception as e:
            logger.error(f"❌ 提取文档ID失败: {str(e)}")
            raise Exception(f"提取文档ID失败: {str(e)}")

        try:
            # 发送请求获取文档页面
            logger.info("📡 正在请求文档页面...")
            response = self.session.get(url, timeout=30, allow_redirects=True, verify=False)

            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"最终URL: {response.url}")
            logger.info(f"响应大小: {len(response.content)} 字节\n")

            if response.status_code != 200:
                logger.error(f"❌ 请求失败，状态码: {response.status_code}")
                raise Exception(f"请求失败，状态码: {response.status_code}")

            # 获取完整HTML内容
            full_html = response.text

            # 解析页面
            soup = BeautifulSoup(full_html, 'html.parser')

            # 提取文档标题
            title = "未知标题"
            title_selectors = [
                'h1.title',
                '.title',
                'title',
                'h1',
                '.article-title'
            ]

            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    if selector == 'title':
                        # 清理title标签中的后缀
                        title = re.sub(r'-.*?CSDN.*?$', '', title).strip()
                    break

            logger.info(f"📄 文档标题: {title}")

            # 检查是否为VIP锁定文档
            is_locked = self.is_vip_wenku_locked(full_html)

            if is_locked:
                logger.info(f"🔒 检测到VIP锁定文档")
                logger.info("正在尝试解锁...")

                # 尝试解锁VIP文档
                unlock_success = self.unlock_vip_wenku(wenku_id)

                if unlock_success:
                    logger.info("🔓 VIP文档解锁成功，重新下载文档内容...")
                    # 重新下载解锁后的内容
                    response = self.session.get(url, timeout=30, verify=False)
                    response.raise_for_status()
                    full_html = response.text

                    # 再次检查是否仍然锁定
                    still_locked = self.is_vip_wenku_locked(full_html)
                    if still_locked:
                        logger.warning("⚠️  VIP文档解锁后仍显示锁定状态")
                    else:
                        logger.info("✅ VIP文档解锁验证成功，内容已完全解锁")
                else:
                    logger.warning("❌ VIP文档解锁失败，将下载锁定状态的内容")
            else:
                logger.info("ℹ️  文档未检测到VIP锁定")

            # 提取文档内容
            content_html = self.extract_wenku_content(full_html)

            return {
                "url": url,
                "title": title,
                "html": full_html,  # 完整HTML
                "content": content_html,  # 文档内容部分
                "wenku_id": wenku_id,
                "is_vip_locked": is_locked,
                "unlock_success": is_locked and unlock_success if is_locked else True
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求异常: {str(e)}")
            raise Exception(f"网络请求异常: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 处理失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            raise Exception(f"处理失败: {str(e)}")

    def extract_wenku_content(self, html_content: str) -> dict:
        """
        从CSDN文库HTML中提取文档内容（Markdown格式）

        Args:
            html_content: 完整的HTML内容

        Returns:
            dict: 包含markdown_text、metadata等信息
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # 优先查找htmledit_views或markdown_views（最精确的内容区域）
        content_area = soup.find('div', class_=lambda x: x and ('htmledit_views' in x or 'markdown_views' in x))
        
        if content_area:
            logger.info(f"✅ 找到精确的文章内容区域: {content_area.get('class')}")
        else:
            # 备用：查找content-view然后移除open按钮
            content_view = soup.find('div', class_='content-view')
            if content_view:
                logger.info(f"✅ 找到content-view区域")
                # 查找并移除"阅读全文"按钮
                open_btn = content_view.find_next_sibling('div', class_='open')
                if open_btn:
                    logger.info(f"🗑️  移除'阅读全文'按钮")
                    open_btn.decompose()
                content_area = content_view
            else:
                # CSDN文库内容的其他可能选择器
                content_selectors = [
                    '.markdown_views',
                    '.answer_content',
                    '.content',
                    'article',
                    '#content',
                    '.article-content'
                ]
                
                for selector in content_selectors:
                    content_area = soup.select_one(selector)
                    if content_area:
                        logger.info(f"✅ 找到文档内容区域: {selector}")
                        break
        
        if not content_area:
            logger.warning("⚠️  未找到明确的内容区域，使用整个body")
            content_area = soup.find('body') or soup
        
        # 提取Markdown文本内容
        markdown_text = content_area.get_text()
        
        # 提取元数据
        metadata = {}
        data_items = soup.find_all('span', class_='data-item')
        for item in data_items:
            text = item.get_text(strip=True)
            if '时间:' in text:
                metadata['publish_time'] = text.replace('时间:', '').strip()
            elif '浏览:' in text:
                metadata['view_count'] = text.replace('浏览:', '').strip()
        
        return {
            'markdown_text': markdown_text,
            'metadata': metadata,
            'html': str(content_area)
        }

    def save_wenku_document(self, url: str, output_dir: str = None) -> dict:
        """
        下载CSDN文库文档并保存为HTML文件

        Args:
            url: 文档URL
            output_dir: 输出目录

        Returns:
            dict: 包含file_path、file_size、title等信息的字典
        """
        # 下载文档
        wenku_data = self.download_wenku_document(url)

        # 确定输出目录
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), "downloads", "wenku")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        title = wenku_data.get('title', '未知标题')
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title).strip()

        if len(safe_title) > 100:
            safe_title = safe_title[:100]

        if not safe_title:
            safe_title = f"wenku_{wenku_data.get('wenku_id', 'unknown')}"

        filename = f"{safe_title}.html"
        file_path = os.path.join(output_dir, filename)

        # 构建完整的HTML文档
        full_html = self.build_wenku_html(wenku_data)

        # 保存HTML文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        logger.info(f"✅ 文档已保存: {file_path}")
        logger.info(f"📊 文件大小: {file_size} 字节")

        return {
            "file_path": file_path,
            "file_size": file_size,
            "title": title,
            "wenku_id": wenku_data.get('wenku_id'),
            "is_vip_locked": wenku_data.get('is_vip_locked'),
            "unlock_success": wenku_data.get('unlock_success')
        }

    def build_wenku_html(self, wenku_data: dict) -> str:
        """
        构建完整的CSDN文库HTML文档（支持Markdown渲染和代码高亮）

        Args:
            wenku_data: 文档数据字典

        Returns:
            str: 完整的HTML文档
        """
        title = wenku_data.get('title', 'CSDN文库文档')
        content_data = wenku_data.get('content', {})
        url = wenku_data.get('url', '')
        
        # 处理旧版返回值（字符串）和新版返回值（字典）
        if isinstance(content_data, str):
            # 旧版本，直接使用HTML内容
            markdown_text = BeautifulSoup(content_data, 'html.parser').get_text()
            metadata = {}
        else:
            # 新版本，包含Markdown文本和元数据
            markdown_text = content_data.get('markdown_text', '')
            metadata = content_data.get('metadata', {})
        
        # 使用markdown库渲染HTML（支持代码块、语法高亮）
        md = markdown.Markdown(extensions=[
            'fenced_code',  # 支持```代码块
            'codehilite',   # 代码语法高亮
            'tables',       # 表格支持
            'nl2br',        # 换行转<br>
        ])
        rendered_content = md.convert(markdown_text)
        
        logger.info(f"🎨 Markdown渲染完成，HTML长度: {len(rendered_content)} 字符")
        
        # 获取元数据信息
        publish_time = metadata.get('publish_time', '未知')
        view_count = metadata.get('view_count', '未知')

        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="source" content="CSDN文库">
    <meta name="original-url" content="{url}">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}

        .header {{
            border-bottom: 2px solid #fc5531;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .title {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        }}

        .metadata {{
            color: #666;
            font-size: 14px;
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #fc5531;
        }}
        
        .metadata p {{
            margin: 5px 0;
        }}

        .content {{
            font-size: 16px;
            line-height: 1.8;
        }}

        /* 代码块样式（GitHub风格） */
        pre {{
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
            font-size: 14px;
            line-height: 1.45;
            margin: 16px 0;
        }}

        code {{
            background: #f6f8fa;
            padding: 3px 6px;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
            font-size: 85%;
            color: #24292f;
        }}
        
        pre code {{
            background: transparent;
            padding: 0;
            border-radius: 0;
            font-size: 14px;
            display: block;
        }}
        
        /* Pygments代码高亮样式 */
        .codehilite {{ 
            background: #f6f8fa; 
            border-radius: 6px; 
            padding: 16px; 
            margin: 16px 0; 
            border: 1px solid #d0d7de;
        }}
        .codehilite pre {{ 
            background: transparent; 
            border: none; 
            padding: 0; 
            margin: 0; 
        }}
        
        /* 语法高亮颜色 */
        .codehilite .c {{ color: #6a737d; font-style: italic; }} /* Comment */
        .codehilite .k {{ color: #d73a49; font-weight: bold; }} /* Keyword */
        .codehilite .s {{ color: #032f62; }} /* String */
        .codehilite .n {{ color: #24292f; }} /* Name */
        .codehilite .o {{ color: #d73a49; }} /* Operator */
        .codehilite .m {{ color: #005cc5; }} /* Number */
        .codehilite .p {{ color: #24292f; }} /* Punctuation */
        .codehilite .nf {{ color: #6f42c1; }} /* Function name */
        .codehilite .c1 {{ color: #6a737d; font-style: italic; }} /* Comment single line */

        blockquote {{
            border-left: 4px solid #4CAF50;
            margin: 16px 0;
            padding-left: 16px;
            color: #666;
        }}

        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}

        th, td {{
            border: 1px solid #d0d7de;
            padding: 8px 12px;
            text-align: left;
        }}

        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        
        /* 段落和列表 */
        p {{ margin: 12px 0; }}
        ul, ol {{ margin: 12px 0; padding-left: 2em; }}
        li {{ margin: 4px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">{title}</h1>
        <div class="metadata">
            <p>📚 来源: CSDN文库</p>
            <p>🔗 原文链接: <a href="{url}" target="_blank">{url}</a></p>
            <p>📅 发布时间: {publish_time}</p>
            <p>👁️ 浏览量: {view_count}</p>
            <p>⏰ 下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <div class="content">
        {rendered_content}
    </div>
</body>
</html>"""

        return html_template

    def close(self):
        """关闭服务，释放session资源"""
        if self.session:
            self.session.close()
            self.session = None