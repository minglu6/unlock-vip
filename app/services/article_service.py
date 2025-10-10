import os
import re
import requests
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .auth_service import AuthService
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ArticleService:
    """文章下载服务 - 使用requests获取文章内容"""

    def __init__(self):
        # 启用验证码自动识别服务
        self.auth_service = AuthService(use_captcha_service=True, debug=False)
        self.is_logged_in = False

    def ensure_login(self):
        """确保已登录"""
        if self.is_logged_in:
            return

        # 尝试加载cookies
        cookies_loaded = self.auth_service.load_cookies()

        if not cookies_loaded:
            # 没有cookies,执行登录
            username = settings.CSDN_USERNAME
            password = settings.CSDN_PASSWORD

            if not username or not password:
                raise Exception("CSDN登录凭证未配置,请在.env文件中设置CSDN_USERNAME和CSDN_PASSWORD")

            login_success = self.auth_service.login(username, password)
            if not login_success:
                raise Exception("CSDN登录失败,请检查用户名和密码")

        # 验证登录状态
        if not self.auth_service.verify_login():
            # cookies失效，重新登录
            username = settings.CSDN_USERNAME
            password = settings.CSDN_PASSWORD

            if not username or not password:
                raise Exception("CSDN登录凭证未配置")

            login_success = self.auth_service.login(username, password)
            if not login_success:
                raise Exception("CSDN登录失败")

        self.is_logged_in = True

    def _force_relogin(self) -> bool:
        """
        强制重新登录，获取新的有效cookies

        Returns:
            bool: 重新登录是否成功
        """
        logger.info("🔄 开始强制重新登录流程...")

        try:
            # 清除当前的登录状态
            self.is_logged_in = False

            # 清除现有的cookies
            if self.auth_service:
                self.auth_service.cookies.clear()

            # 重新执行完整的登录流程
            username = settings.CSDN_USERNAME
            password = settings.CSDN_PASSWORD

            if not username or not password:
                logger.error("❌ CSDN登录凭证未配置，无法重新登录")
                return False

            logger.info(f"📝 使用用户名 {username} 重新登录...")

            # 执行登录
            login_success = self.auth_service.login(username, password)

            if login_success:
                logger.info("✅ 重新登录成功")

                # 验证新的登录状态
                if self.auth_service.verify_login():
                    logger.info("✅ 新的登录状态验证通过")
                    self.is_logged_in = True
                    return True
                else:
                    logger.warning("⚠️  新的登录状态验证失败，但登录过程成功")
                    self.is_logged_in = True
                    return True
            else:
                logger.error("❌ 重新登录失败")
                return False

        except Exception as e:
            logger.error(f"❌ 重新登录过程出错: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return False

    def extract_article_id(self, url: str) -> str:
        """
        从文章URL中提取文章ID

        Args:
            url: 文章URL，例如 https://blog.csdn.net/username/article/details/151638092

        Returns:
            str: 文章ID
        """
        # 使用正则表达式提取文章ID
        match = re.search(r'/article/details/(\d+)', url)
        if match:
            return match.group(1)

        # 检查是否是wenku.csdn.net的URL
        if 'wenku.csdn.net' in url:
            # 提取wenku文档ID，支持多种格式
            wenku_match = re.search(r'wenku\.csdn\.net/(answer|doc|column)/([a-zA-Z0-9_-]+)', url)
            if wenku_match:
                return wenku_match.group(2)
            # 尝试其他可能的格式
            wenku_match = re.search(r'wenku\.csdn\.net/[^/]+/([a-zA-Z0-9_-]+)', url)
            if wenku_match:
                return wenku_match.group(1)

        raise Exception(f"无法从URL中提取文章ID: {url}")

    def unlock_vip_article(self, article_id: str, retry_with_login: bool = True) -> bool:
        """
        解锁VIP文章 - 调用CSDN解锁API

        Args:
            article_id: 文章ID
            retry_with_login: 当遇到401错误时是否重新登录后重试

        Returns:
            bool: 是否解锁成功
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔓 开始解锁VIP文章")
        logger.info(f"{'='*60}")
        logger.info(f"📄 文章ID: {article_id}")

        # 直接加载cookies文件，确保使用最新的有效cookies
        try:
            with open('cookies.json', 'r', encoding='utf-8') as f:
                cookies_dict = json.load(f)

            logger.info(f"成功加载cookies文件，共{len(cookies_dict)}个cookies")
            logger.info(f"关键cookies - UserToken: {cookies_dict.get('UserToken', 'NOT_FOUND')[:20]}...")

            # 创建新的session，直接加载cookies
            session = requests.Session()

            # 设置cookies到正确的域
            for name, value in cookies_dict.items():
                session.cookies.set(name, value, domain='.csdn.net')

            # 设置完整的请求头（复刻成功测试脚本的配置）
            session.headers.update({
                'Accept': '*/*',
                'Content-Type': 'application/json; charset=UTF-8',
                'Origin': 'https://blog.csdn.net',
                'Referer': f'https://blog.csdn.net/article/details/{article_id}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            })

            logger.info(f"Cookies数量: {len(session.cookies)}")
            logger.info(f"关键cookies存在检查:")
            has_user_token = any(cookie.name == 'UserToken' for cookie in session.cookies)
            has_user_info = any(cookie.name == 'UserInfo' for cookie in session.cookies)
            logger.info(f"   UserToken: {has_user_token}, UserInfo: {has_user_info}")

            # 🔑 发送解锁请求
            unlock_url = "https://blog.csdn.net/phoenix/web/v1/vip-article-read"
            payload = {"articleId": int(article_id)}
            
            logger.info(f"解锁接口: {unlock_url}")
            logger.info(f"请求数据: {json.dumps(payload)}")
            logger.info(f"发送解锁请求...")
            
            response = session.post(unlock_url, json=payload, timeout=30, verify=False)
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text[:500]}")
            
            try:
                result = response.json()
                logger.info(f"📨 API响应: {json.dumps(result, ensure_ascii=False)}")
                
                if result.get('code') == 200:
                    logger.info(f"✅ VIP文章解锁成功！")
                    logger.info(f"{'='*60}\n")
                    return True
                elif result.get('code') == 400:
                    # 400 通常表示文章不是VIP文章，或已解锁
                    logger.info(f"ℹ️  文章可能不是VIP文章或已解锁")
                    logger.info(f"{'='*60}\n")
                    return True
                else:
                    logger.warning(f"⚠️  解锁失败: code={result.get('code')}, message={result.get('message')}")
                    logger.info(f"{'='*60}\n")
                    return False
                    
            except json.JSONDecodeError:
                logger.warning(f"解锁API返回非JSON响应: {response.text[:100]}")
                logger.info(f"{'='*60}\n")
                # 无法解析响应，可能需要重新登录
                if retry_with_login:
                    logger.info("尝试使用回退方法...")
                    return self._unlock_vip_article_fallback(article_id, retry_with_login=False)
                else:
                    return False

        except Exception as e:
            logger.error(f"加载cookies失败: {str(e)}")
            # 回退到原来的方法
            return self._unlock_vip_article_fallback(article_id, retry_with_login)

    def _unlock_vip_article_fallback(self, article_id: str, retry_with_login: bool = True) -> bool:
        """
        解锁VIP文章的回退方法 - 使用auth_service的session
        """
        logger.info(f"🔄 使用回退方法解锁VIP文章")

        self.ensure_login()
        session = self.auth_service.get_session()

        # 解锁接口URL
        unlock_url = "https://blog.csdn.net/phoenix/web/v1/vip-article-read"
        logger.info(f"解锁接口: {unlock_url}")

        # 请求头
        session.headers.update({
            'Accept': '*/*',
            'Content-Type': 'application/json; charset=UTF-8',
            'Origin': 'https://blog.csdn.net',
            'Referer': f'https://blog.csdn.net/article/details/{article_id}',
            'X-Requested-With': 'XMLHttpRequest',
        })

        # 请求体
        payload = {"articleId": int(article_id)}
        logger.info(f"请求数据: {json.dumps(payload)}")

        try:
            logger.info(f"发送解锁请求...")
            response = session.post(unlock_url, json=payload, timeout=30, verify=False)

            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text[:500]}")

            try:
                result = response.json()
                logger.info(f"解析后的响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

                if result.get('code') == 200:
                    logger.info(f"VIP文章解锁成功！")
                    logger.info(f"{'='*60}\n")
                    return True
                else:
                    logger.warning(f"解锁失败: code={result.get('code')}, message={result.get('message')}")
                    logger.info(f"{'='*60}\n")
                    # 即使响应不是200，也尝试继续下载
                    return True

            except json.JSONDecodeError:
                # 如果响应不是有效的JSON，可能是空响应
                logger.warning(f"解锁API返回非JSON响应: {response.text[:100]}")
                logger.warning("这可能意味着账号没有VIP权限或cookies已过期")

                # 强制重新登录获取新的VIP会话
                logger.info("尝试强制重新登录获取有效VIP会话...")

                from app.core.config import settings
                username = settings.CSDN_USERNAME
                password = settings.CSDN_PASSWORD

                if username and password:
                    login_success = self.auth_service.login(username, password)
                    if login_success:
                        logger.info("重新登录成功，重试解锁...")
                        # 使用新的cookies重试解锁
                        return self.unlock_vip_article(article_id, retry_with_login=False)
                    else:
                        logger.error("重新登录失败，无法解锁VIP文章")
                        return False
                else:
                    logger.error("CSDN登录凭证未配置，无法重新登录")
                    return False

        except Exception as e:
            logger.error(f"回退方法也失败: {str(e)}")
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

            session = self.auth_service.get_session()

            for unlock_url in unlock_urls:
                try:
                    logger.info(f"尝试解锁接口: {unlock_url}")

                    # 设置请求头
                    session.headers.update({
                        'Accept': '*/*',
                        'Content-Type': 'application/json; charset=UTF-8',
                        'Origin': 'https://wenku.csdn.net',
                        'Referer': f'https://wenku.csdn.net/answer/{wenku_id}',
                        'X-Requested-With': 'XMLHttpRequest',
                    })

                    response = session.post(unlock_url, json=payload, timeout=30, verify=False)

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

    def is_vip_article_locked(self, html_content: str, url: str = "") -> bool:
        """
        检测文章是否为VIP锁定状态（针对具体接口优化）

        对于带cookies访问的wenku接口，通常不会有锁定标识，
        此方法主要用于日志记录和兼容性检测

        Args:
            html_content: 文章HTML内容
            url: 文章URL，用于区分博客和文库

        Returns:
            bool: 是否为VIP锁定状态
        """
        if 'wenku.csdn.net' in url:
            # 针对具体的wenku/answer接口，轻量级检测
            # 因为带cookies访问通常已解锁，只需记录异常状态

            # 快速文本检测，无需复杂DOM解析
            content_lower = html_content.lower()

            # 检查是否存在明显的VIP锁定标识
            vip_indicators = [
                '开通会员查看完整答案',
                '最低0.3元/天',
                '阅读全文',
                'class="open-btn-wrap"',
                'data-vip="true"'
            ]

            for indicator in vip_indicators:
                if indicator.lower() in content_lower:
                    logger.info(f"检测到可能的VIP标识: {indicator}")
                    return True

            # 对于wenku接口，默认认为已解锁
            return False

        else:
            # CSDN博客的VIP锁定检测（保持原有逻辑）
            vip_lock_indicators = [
                'class="vip-mask"',
                'class="read-all-content-btn"',
                'vip-article-read',
                'data-vip="true"',
                'vip-lock',
                'vip-mask'
            ]

            content_lower = html_content.lower()

            for indicator in vip_lock_indicators:
                if indicator.lower() in content_lower:
                    logger.info(f"检测到CSDN博客VIP锁定标志: {indicator}")
                    return True

            return False

    def download_article(self, url: str) -> dict:
        """
        下载CSDN文章HTML - 支持VIP文章解锁检测

        Args:
            url: 文章URL

        Returns:
            dict: 包含url、title、html的字典
        """
        self.ensure_login()

        # 提取文章ID
        try:
            article_id = self.extract_article_id(url)
        except Exception as e:
            logger.error(f"提取文章ID失败: {str(e)}")
            article_id = None

        # 添加完整的请求头，模拟真实浏览器
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Referer': url,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        def build_session() -> requests.Session:
            new_session = self.auth_service.get_session()
            new_session.headers.update(headers)
            return new_session

        def fetch_html(current_session: requests.Session) -> str:
            logger.info(f"正在下载文章页面: {url}")
            response = current_session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            return response.text

        session = build_session()
        unlock_success = False

        try:
            full_html = fetch_html(session)

            # 检查是否为VIP锁定文章
            # 对于带cookies访问，正常情况下不应有锁定标识
            # 如果检测到锁定标识，可能意味着cookie已失效
            is_locked = self.is_vip_article_locked(full_html, url)
            if is_locked:
                logger.warning("⚠️  检测到VIP锁定标识，尝试执行解锁流程")

                if article_id:
                    logger.info("� 调用VIP解锁接口...")
                    unlock_success = self.unlock_vip_article(article_id)
                    if unlock_success:
                        logger.info("✅ VIP解锁成功，刷新文章内容")
                        session = build_session()
                        full_html = fetch_html(session)
                        is_locked = self.is_vip_article_locked(full_html, url)

                if is_locked and not unlock_success:
                    logger.info("🔄 尝试重新登录获取有效cookies...")
                    try:
                        if self._force_relogin():
                            logger.info("✅ 重新登录成功，刷新会话")
                            session = build_session()

                            if article_id:
                                unlock_success = self.unlock_vip_article(article_id)

                            full_html = fetch_html(session)
                            is_locked = self.is_vip_article_locked(full_html, url)

                            if is_locked:
                                logger.error("❌ 重新登录后仍检测到VIP锁定，可能账号无权限或页面结构变化")
                            else:
                                logger.info("✅ 重新登录后VIP锁定解除")
                        else:
                            logger.error("❌ 重新登录失败，继续使用当前cookies")
                    except Exception as login_error:
                        logger.error(f"❌ 重新登录过程出错: {str(login_error)}")
            else:
                logger.info("✅ 未检测到VIP锁定，正常处理文档")

            # 解析HTML
            soup = BeautifulSoup(full_html, 'html.parser')

            # 提取文章标题
            title = "未知标题"
            title_selectors = [
                'h1.title-article',
                '.article-title',
                'h1[class*="title"]',
                'article h1'
            ]

            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break

            # 提取文章内容
            article_content = None

            # 根据URL类型选择不同的内容选择器
            if 'wenku.csdn.net' in url:
                # 针对具体的wenku/answer接口优化内容提取
                # 基于已知的具体接口结构
                content_selectors = [
                    '.markdown_views',      # 主要的markdown内容区域
                    '.content-view',        # 内容视图容器
                    '.answer_content',      # 回答内容区域
                    'div.markdown_views',   # 具体的markdown容器
                    '.content',             # 通用内容区域
                    'article',              # 文章容器
                ]
            else:
                # CSDN博客内容选择器
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
                    logger.info(f"✅ 找到内容区域: {selector}")

                    # 针对wenku的特殊处理：移除可能的遮盖元素
                    if 'wenku.csdn.net' in url:
                        # 清理内容中的遮盖元素
                        content_soup = BeautifulSoup(article_content, 'html.parser')

                        # 移除"阅读全文"相关元素
                        for overlay in content_soup.find_all(class_=['open', 'open-btn', 'open-btn-wrap']):
                            overlay.decompose()

                        # 移除高度限制
                        for container in content_soup.find_all(class_=['cont', 'content-view']):
                            if 'first-show' in container.get('class', []):
                                container['class'].remove('first-show')
                            if container.get('style'):
                                container['style'] = re.sub(r'(max-)?height:\s*\d+px[^;]*;?', '', container['style'])

                        article_content = str(content_soup)

                    break

            # 如果没有找到文章内容，返回整个页面
            if not article_content:
                article_content = full_html

            return {
                "url": url,
                "title": title,
                "html": full_html,  # 完整HTML（可能是解锁后的）
                "content": article_content,  # 文章内容部分
                "is_vip_locked": is_locked and article_id and not unlock_success  # VIP锁定状态
            }

        except requests.exceptions.Timeout:
            logger.error("❌ 请求超时")
            raise Exception("下载文章失败: 请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            logger.error("❌ 连接失败")
            raise Exception("下载文章失败: 无法连接到服务器")
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP错误: {e.response.status_code}")
            raise Exception(f"下载文章失败: HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求错误: {str(e)}")
            raise Exception(f"下载文章失败: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 解析文章失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            raise Exception(f"解析文章失败: {str(e)}")

    def extract_clean_content(self, html_content: str, title: str = "", url: str = "") -> str:
        """
        从完整HTML中提取纯净的文章内容，保持CSDN原版样式

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
                # CSDN文库标题提取
                title_elem = soup.find('h1', class_='title')
                if not title_elem:
                    title_elem = soup.find('h1')
                if not title_elem:
                    title_elem = soup.find('title')
            else:
                # CSDN博客标题提取
                title_elem = soup.find('h1', class_='title-article')

            if title_elem:
                title = title_elem.get_text().strip()
                # 清理title标签中的后缀
                title = re.sub(r'-.*?CSDN.*?$', '', title).strip()
            else:
                title = "文章内容"

        # 根据URL类型选择不同的内容区域
        if 'wenku.csdn.net' in url:
            # CSDN文库内容提取
            content_div = soup.find('div', class_='markdown_views')
            if not content_div:
                content_div = soup.find('div', class_='content-view')
            if not content_div:
                content_div = soup.find('div', class_='answer_content')
            if not content_div:
                content_div = soup.find('div', class_='content')
        else:
            # CSDN博客内容提取
            content_div = soup.find('div', {'id': 'content_views'})
            if not content_div:
                content_div = soup.find('div', {'class': 'article_content'})

        if not content_div:
            # 如果找不到内容区域，返回原始HTML
            return html_content

        # 清理不需要的元素
        for element in content_div.find_all(['script', 'iframe', 'noscript']):
            element.decompose()

        # 移除广告和推荐相关的div
        for element in content_div.find_all(['div', 'section'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['ad', 'advert', 'recommend', 'relate', 'comment']
        )):
            element.decompose()

        # 提取CSDN原版CSS样式链接
        csdn_styles = []
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            # 只保留CSDN相关的样式文件
            if 'csdnimg.cn' in href or 'csdn.net' in href:
                if any(keyword in href for keyword in ['markdown_views', 'editerView', 'prism', 'highlight']):
                    csdn_styles.append(href)

        # 获取清理后的内容HTML
        clean_content_html = str(content_div)

        # 构建样式链接
        style_links = '\n    '.join([f'<link rel="stylesheet" href="{url}">' for url in csdn_styles])

        # 创建HTML页面，保持CSDN原版样式
        clean_html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {style_links}
    <style>
        body {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }}
        #content_views {{
            font-size: 16px;
            line-height: 1.8;
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

        # 生成文件名（使用标题）
        title = article_data.get('title', '未知标题')
        # 清理标题中的非法字符（保留中文、英文、数字、常见符号）
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)  # 移除Windows文件名非法字符
        safe_title = safe_title.strip()

        # 限制文件名长度
        if len(safe_title) > 100:
            safe_title = safe_title[:100]

        # 如果标题为空，使用默认名称
        if not safe_title:
            safe_title = "文章"

        filename = f"{safe_title}.html"
        file_path = os.path.join(output_dir, filename)

        # 保存HTML文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(clean_html)

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        return {
            "file_path": file_path,
            "file_size": file_size,
            "title": title
        }

    def close(self):
        """关闭服务"""
        self.auth_service.close()