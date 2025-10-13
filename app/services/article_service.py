"""
CSDN文章下载服务
仅使用cookies.json进行身份验证，通过requests模拟浏览器请求
不包含自动登录、Playwright等复杂功能
"""
import os
import re
import json
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ArticleService:
    """文章下载服务 - 基于cookies的简化版本"""

    def __init__(self, cookies_file: str = 'cookies.json'):
        """
        初始化文章服务

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

        # 加载cookies文件
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies_dict = json.load(f)

            # 设置cookies到正确的域
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value, domain='.csdn.net')

            # 设置请求头，模拟真实浏览器
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            })

            logger.info("成功加载cookies并初始化session")

        except FileNotFoundError:
            logger.error(f"cookies文件不存在: {self.cookies_file}")
            raise Exception(f"cookies文件不存在: {self.cookies_file}，请先手动获取cookies")
        except Exception as e:
            logger.error(f"加载cookies失败: {str(e)}")
            raise Exception(f"加载cookies失败: {str(e)}")

    def extract_article_id(self, url: str) -> str:
        """
        从文章URL中提取文章ID

        Args:
            url: 文章URL，例如 https://blog.csdn.net/username/article/details/151638092

        Returns:
            str: 文章ID
        """
        # 博客文章ID
        match = re.search(r'/article/details/(\d+)', url)
        if match:
            return match.group(1)

        # 文库文档ID
        if 'wenku.csdn.net' in url:
            wenku_match = re.search(r'wenku\.csdn\.net/(answer|doc|column)/([a-zA-Z0-9_-]+)', url)
            if wenku_match:
                return wenku_match.group(2)
            wenku_match = re.search(r'wenku\.csdn\.net/[^/]+/([a-zA-Z0-9_-]+)', url)
            if wenku_match:
                return wenku_match.group(1)

        raise Exception(f"无法从URL中提取文章ID: {url}")

    def unlock_vip_article(self, article_id: str) -> bool:
        """
        解锁VIP文章 - 调用CSDN解锁API

        Args:
            article_id: 文章ID

        Returns:
            bool: 是否解锁成功
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"开始解锁VIP文章")
        logger.info(f"{'='*60}")
        logger.info(f"文章ID: {article_id}")

        self._load_session()

        # 解锁接口URL
        unlock_url = "https://blog.csdn.net/phoenix/web/v1/vip-article-read"

        # 设置请求头
        self.session.headers.update({
            'Accept': '*/*',
            'Content-Type': 'application/json; charset=UTF-8',
            'Origin': 'https://blog.csdn.net',
            'Referer': f'https://blog.csdn.net/article/details/{article_id}',
            'X-Requested-With': 'XMLHttpRequest',
        })

        # 请求体
        payload = {"articleId": int(article_id)}

        try:
            logger.info(f"发送解锁请求...")
            response = self.session.post(unlock_url, json=payload, timeout=30, verify=False)

            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text[:500]}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"API响应: {json.dumps(result, ensure_ascii=False)}")

                    if result.get('code') == 200:
                        logger.info(f"VIP文章解锁成功")
                        logger.info(f"{'='*60}\n")
                        return True
                    elif result.get('code') == 400:
                        logger.info(f"文章可能不是VIP文章或已解锁")
                        logger.info(f"{'='*60}\n")
                        return True
                    else:
                        logger.warning(f"解锁失败: code={result.get('code')}, message={result.get('message')}")
                        logger.info(f"{'='*60}\n")
                        return False

                except json.JSONDecodeError:
                    logger.warning(f"解锁API返回非JSON响应: {response.text[:100]}")
                    logger.info(f"{'='*60}\n")
                    return False

        except Exception as e:
            logger.error(f"解锁VIP文章失败: {str(e)}")
            logger.info(f"{'='*60}\n")
            return False

    def is_vip_article_locked(self, html_content: str, url: str = "") -> bool:
        """
        检测文章是否为VIP锁定状态

        Args:
            html_content: 文章HTML内容
            url: 文章URL，用于区分博客和文库

        Returns:
            bool: 是否为VIP锁定状态
        """
        content_lower = html_content.lower()

        if 'wenku.csdn.net' in url:
            # 文库VIP锁定标识
            vip_indicators = [
                '开通会员查看完整答案',
                '最低0.3元/天',
                '阅读全文',
                'class="open-btn-wrap"',
                'data-vip="true"'
            ]
        else:
            # 博客VIP锁定标识
            vip_indicators = [
                'class="vip-mask"',
                'class="read-all-content-btn"',
                'vip-article-read',
                'data-vip="true"',
                'vip-lock',
                'vip-mask'
            ]

        for indicator in vip_indicators:
            if indicator.lower() in content_lower:
                logger.info(f"检测到VIP锁定标志: {indicator}")
                return True

        return False

    def download_article(self, url: str) -> dict:
        """
        下载CSDN文章HTML - 支持VIP文章解锁检测

        Args:
            url: 文章URL

        Returns:
            dict: 包含url、title、html、content的字典
        """
        self._load_session()

        # 提取文章ID
        try:
            article_id = self.extract_article_id(url)
        except Exception as e:
            logger.error(f"提取文章ID失败: {str(e)}")
            article_id = None

        try:
            logger.info(f"正在下载文章页面: {url}")
            response = self.session.get(url, timeout=30, verify=False)

            if response.status_code != 200:
                logger.warning(f"请求返回非200状态码: {response.status_code}")
                raise requests.exceptions.HTTPError(f"HTTP {response.status_code}")

            full_html = response.text

            # 检查是否为VIP锁定文章
            is_locked = self.is_vip_article_locked(full_html, url)

            if is_locked and article_id:
                logger.warning("检测到VIP锁定标识，尝试解锁")
                unlock_success = self.unlock_vip_article(article_id)

                if unlock_success:
                    logger.info("VIP解锁成功，重新下载文章内容")
                    response = self.session.get(url, timeout=30, verify=False)
                    full_html = response.text
                    is_locked = self.is_vip_article_locked(full_html, url)

            # 解析HTML
            soup = BeautifulSoup(full_html, 'html.parser')

            # 提取文章标题
            title = "未知标题"
            if 'wenku.csdn.net' in url:
                title_selectors = ['h1.title', '.title', 'h1', 'title']
            else:
                title_selectors = ['h1.title-article', '.article-title', 'h1[class*="title"]', 'article h1']

            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    if selector == 'title':
                        title = re.sub(r'-.*?CSDN.*?$', '', title).strip()
                    break

            # 提取文章内容
            article_content = None

            if 'wenku.csdn.net' in url:
                # 文库内容选择器
                content_selectors = [
                    '.markdown_views',
                    '.content-view',
                    '.answer_content',
                    'div.markdown_views',
                    '.content',
                    'article'
                ]
            else:
                # 博客内容选择器
                content_selectors = [
                    '#article_content',
                    '.article_content',
                    'article',
                    '.blog-content-box'
                ]

            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    article_content = str(content_element)
                    logger.info(f"找到内容区域: {selector}")

                    # 文库特殊处理：移除遮盖元素
                    if 'wenku.csdn.net' in url:
                        content_soup = BeautifulSoup(article_content, 'html.parser')
                        for overlay in content_soup.find_all(class_=['open', 'open-btn', 'open-btn-wrap']):
                            overlay.decompose()
                        for container in content_soup.find_all(class_=['cont', 'content-view']):
                            if 'first-show' in container.get('class', []):
                                container['class'].remove('first-show')
                            if container.get('style'):
                                container['style'] = re.sub(r'(max-)?height:\s*\d+px[^;]*;?', '', container['style'])
                        article_content = str(content_soup)

                    break

            if not article_content:
                article_content = full_html

            return {
                "url": url,
                "title": title,
                "html": full_html,
                "content": article_content,
                "is_vip_locked": is_locked and article_id
            }

        except requests.exceptions.Timeout:
            logger.error("请求超时")
            raise Exception("下载文章失败: 请求超时")
        except requests.exceptions.ConnectionError:
            logger.error("连接失败")
            raise Exception("下载文章失败: 无法连接到服务器")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {e}")
            raise Exception(f"下载文章失败: HTTP错误")
        except Exception as e:
            logger.error(f"解析文章失败: {str(e)}")
            raise Exception(f"解析文章失败: {str(e)}")

    def extract_clean_content(self, html_content: str, title: str = "", url: str = "") -> str:
        """
        从完整HTML中提取纯净的文章内容

        Args:
            html_content: 完整的HTML内容
            title: 文章标题
            url: 文章URL，用于区分博客和文库

        Returns:
            str: 清理后的HTML内容
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取文章标题（如果未提供）
        if not title:
            if 'wenku.csdn.net' in url:
                title_elem = soup.find('h1', class_='title') or soup.find('h1') or soup.find('title')
            else:
                title_elem = soup.find('h1', class_='title-article')

            if title_elem:
                title = title_elem.get_text().strip()
                title = re.sub(r'-.*?CSDN.*?$', '', title).strip()
            else:
                title = "文章内容"

        # 根据URL类型选择不同的内容区域
        if 'wenku.csdn.net' in url:
            content_div = (soup.find('div', class_='markdown_views') or
                          soup.find('div', class_='content-view') or
                          soup.find('div', class_='answer_content') or
                          soup.find('div', class_='content'))
        else:
            content_div = (soup.find('div', {'id': 'content_views'}) or
                          soup.find('div', {'class': 'article_content'}))

        if not content_div:
            return html_content

        # 清理不需要的元素
        for element in content_div.find_all(['script', 'iframe', 'noscript']):
            element.decompose()

        # 移除广告和推荐
        for element in content_div.find_all(['div', 'section'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['ad', 'advert', 'recommend', 'relate', 'comment']
        )):
            element.decompose()

        # 获取清理后的内容HTML
        clean_content_html = str(content_div)

        # 创建HTML页面
        clean_html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #fc5531;
            padding-bottom: 10px;
        }}
        #content_views {{
            font-size: 16px;
            line-height: 1.8;
        }}
        pre {{
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
        }}
        code {{
            background: #f6f8fa;
            padding: 3px 6px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {clean_content_html}
</body>
</html>
"""
        return clean_html_template

    def save_article(self, url: str, output_dir: str = None) -> dict:
        """
        下载CSDN文章并保存为HTML文件

        Args:
            url: 文章URL
            output_dir: 输出目录，默认为 downloads 文件夹

        Returns:
            dict: 包含file_path、file_size、title的字典
        """
        # 下载文章
        article_data = self.download_article(url)

        # 提取纯净内容
        clean_html = self.extract_clean_content(
            article_data['html'],
            article_data.get('title', '未知标题'),
            url
        )

        # 确定输出目录
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), "downloads")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        title = article_data.get('title', '未知标题')
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title).strip()

        if len(safe_title) > 100:
            safe_title = safe_title[:100]

        if not safe_title:
            safe_title = "文章"

        filename = f"{safe_title}.html"
        file_path = os.path.join(output_dir, filename)

        # 保存HTML文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(clean_html)

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        logger.info(f"文章已保存: {file_path}")
        logger.info(f"文件大小: {file_size} 字节")

        return {
            "file_path": file_path,
            "file_size": file_size,
            "title": title
        }

    def close(self):
        """关闭服务，释放session资源"""
        if self.session:
            self.session.close()
            self.session = None
