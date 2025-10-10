import json
import os
import shutil
import time
import random
from typing import Dict, Optional

from playwright.sync_api import (
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from app.core.config import settings
from app.services.captcha_service import get_captcha_service
from app.utils.stealth_utils import (
    apply_stealth_to_page,
    get_latest_chrome_ua,
    get_random_viewport,
    get_stealth_launch_args,
    simulate_human_delay,
    handle_521_error,
)


class AuthService:
    """CSDN认证服务 - 使用Playwright模拟浏览器登录"""

    def __init__(self, use_captcha_service: bool = False, debug: bool = False):
        """
        初始化认证服务

        Args:
            use_captcha_service: 是否使用第三方验证码识别服务
            debug: 是否开启调试模式（保存截图和HTML）
        """
        self.cookies_file = "cookies.json"
        self.cookies: Dict[str, str] = {}
        self.playwright = None
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.user_data_dir: Optional[str] = None
        self.use_captcha_service = use_captcha_service
        self.debug = debug

        if use_captcha_service:
            self.captcha_service = self._init_captcha_service()
        else:
            self.captcha_service = None

    def _cleanup_user_data_dir(self):
        """清理用户数据目录"""
        # 当启用持久化指纹时，不清理目录
        persist_dir = os.getenv("PW_USER_DATA_DIR") or os.getenv("PLAYWRIGHT_USER_DATA_DIR")
        should_persist = bool(persist_dir) or os.getenv("PW_PERSIST_PROFILE", "1") == "1"
        if should_persist:
            return
        if self.user_data_dir and os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir)
                print(f"[Clean] 已清理旧的 user-data-dir: {self.user_data_dir}")
            except Exception as exc:
                print(f"[WARN] 清理 user-data-dir 失败: {exc}")
        self.user_data_dir = None

    def _init_captcha_service(self):
        """初始化验证码识别服务"""
        service_type = settings.CAPTCHA_SERVICE

        if service_type == 'chaojiying':
            svc = get_captcha_service(
                'chaojiying',
                username=settings.CHAOJIYING_USERNAME,
                password=settings.CHAOJIYING_PASSWORD,
                soft_id=settings.CHAOJIYING_SOFT_ID,
            )
            print("[Captcha] 使用 ChaoJiYing 服务")
            return svc
        if service_type == '2captcha':
            svc = get_captcha_service(
                '2captcha',
                api_key=settings.TWOCAPTCHA_API_KEY,
            )
            print("[Captcha] 使用 2Captcha 服务")
            return svc
        if service_type == 'mock':
            print("[Captcha] 使用 Mock 验证码服务（仅调试）")
            return get_captcha_service('mock')

        print(f"[WARN] 未知的验证码服务类型: {service_type}，将使用手动模式")
        return None

    def _init_browser(self):
        """启动 Playwright Chromium 浏览器"""
        import tempfile

        # 先确保其它会话已经关闭
        self.close()

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            self._cleanup_user_data_dir()
            # 计算持久化目录：优先 PW_USER_DATA_DIR，其次 /tmp/pw_profile，最后临时目录
            env_profile = os.getenv("PW_USER_DATA_DIR") or os.getenv("PLAYWRIGHT_USER_DATA_DIR")
            if env_profile:
                self.user_data_dir = env_profile
            else:
                # 默认开启轻度持久化，减少新设备指纹命中
                default_profile = os.path.join(tempfile.gettempdir(), "pw_profile")
                self.user_data_dir = default_profile
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)
            except Exception:
                # 回退到真正的临时目录
                self.user_data_dir = tempfile.mkdtemp(prefix="pw_user_data_")

            try:
                self.playwright = sync_playwright().start()

                # 使用stealth工具获取优化的启动参数
                launch_args = get_stealth_launch_args()

                extra_args = os.getenv("PLAYWRIGHT_EXTRA_ARGS")
                if extra_args:
                    launch_args.extend(arg for arg in extra_args.split() if arg)

                headless = os.getenv("PLAYWRIGHT_HEADFUL", "0") != "1"

                # 获取随机viewport和最新UA
                viewport_dict = get_random_viewport()
                user_agent = get_latest_chrome_ua()

                print(f"[Stealth] 使用viewport: {viewport_dict['width']}x{viewport_dict['height']}")
                print(f"[Stealth] 使用UA: Chrome 131.0.0.0")

                context = self.playwright.chromium.launch_persistent_context(
                    self.user_data_dir,
                    headless=headless,
                    args=launch_args,
                    viewport={'width': viewport_dict['width'], 'height': viewport_dict['height']},
                    ignore_https_errors=True,
                    user_agent=user_agent,
                    bypass_csp=True,
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                    # 添加现代浏览器特征
                    extra_http_headers={
                        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'DNT': '1',
                    },
                    ignore_default_args=['--enable-automation'],
                )

                # 应用stealth脚本
                context.add_init_script("""
                    // 隐藏webdriver
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

                    // 模拟Chrome对象
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };

                    // 隐藏自动化特征
                    delete navigator.__proto__.webdriver;
                """)

                self.browser_context = context
                self.page = context.pages[0] if context.pages else context.new_page()

                # 应用stealth插件到页面
                print("[Stealth] 应用反检测配置到页面...")
                apply_stealth_to_page(self.page)

                # 放宽默认等待与导航超时，适配云服务器网络波动
                try:
                    self.page.set_default_timeout(30000)
                    self.page.set_default_navigation_timeout(30000)
                except Exception:
                    pass

                # 轻量化资源加载：可选拦截 字体/媒体（不拦图片，避免影响验证码）
                try:
                    block_media_fonts = os.getenv("PLAYWRIGHT_BLOCK_MEDIA_FONTS", "0") == "1"
                    if block_media_fonts:
                        print("[Net] 资源拦截启用：拦截 font/media，放行 image/js/css")
                    else:
                        print("[Net] 资源拦截已禁用：放行所有资源")

                    def _route_filter(route, request):
                        try:
                            rtype_attr = getattr(request, 'resource_type', None)
                            rtype = rtype_attr() if callable(rtype_attr) else rtype_attr
                        except Exception:
                            rtype = None
                        # 若禁用拦截，则直接放行
                        if not block_media_fonts:
                            return route.continue_()
                        # 不拦图片，避免影响验证码加载；仅拦字体/媒体
                        if rtype in ("media", "font"):
                            route.abort()
                        else:
                            route.continue_()

                    self.page.route("**/*", _route_filter)
                    try:
                        # 对齐语言偏好
                        context.set_extra_http_headers({"Accept-Language": "zh-CN,zh;q=0.9"})
                    except Exception:
                        pass
                except Exception:
                    pass

                print(f"[OK] Chromium 启动成功 (尝试 {attempt}/{max_retries})")
                return
            except PlaywrightError as exc:
                print(f"[ERROR] Chromium 启动失败 (尝试 {attempt}/{max_retries}): {str(exc)[:120]}")
                self.close()
                if attempt == max_retries:
                    raise
                time.sleep(2)

    def login(self, username: str, password: str) -> bool:
        """
        使用用户名密码登录CSDN

        Args:
            username: 用户名（手机号或邮箱）
            password: 密码

        Returns:
            bool: 登录是否成功
        """
        try:
            self._init_browser()

            if not self.page:
                print("[ERROR] 浏览器页面初始化失败")
                return False

            page = self.page

            print("[Net] 正在访问CSDN登录页面...")
            login_url = 'https://passport.csdn.net/login?code=applets'

            # 使用智能重试处理521等错误
            if not handle_521_error(page, login_url, max_retries=3):
                print("[ERROR] 无法访问登录页面，可能被Cloudflare/WAF拦截")
                return False

            # 模拟人类行为：随机延迟
            print("[Stealth] 模拟人类浏览行为...")
            simulate_human_delay(1000, 2500)
            # 扫码登录模式（通过环境变量控制）
            try:
                scan_enabled = os.getenv("LOGIN_SCAN_WECHAT", "0") == "1"
                if scan_enabled:
                    wait_secs = int(os.getenv("LOGIN_SCAN_WAIT", "30"))
                    ok = self._attempt_scan_login(wait_ms=wait_secs * 1000)
                    current_url = page.url
                    print(f"[Location] 当前页面URL: {current_url}")
                    if ok and ('login' not in current_url and 'passport' not in current_url):
                        print("[OK] 登录成功！（扫码）")
                        if self.browser_context:
                            context_cookies = self.browser_context.cookies()
                            self.cookies = {item['name']: item['value'] for item in context_cookies}
                            print(f"[Note] 获取到 {len(self.cookies)} 个cookie")
                            self._save_cookies()
                        return True
                    else:
                        print("[ERROR] 扫码模式登录失败或超时")
                        return False
            except Exception:
                pass

            print("[Search] 尝试切换到验证码登录模式...")
            try:
                verification_login_tab = page.locator("text=验证码登录")
                if verification_login_tab.count() > 0:
                    verification_login_tab.first.click()
                    page.wait_for_timeout(2000)
            except PlaywrightError as exc:
                print(f"  未找到验证码登录标签: {str(exc)[:80]}")

            print("[Search] 查找其他登录方式...")
            try:
                other_login_elements = page.locator("text=其他登录方式")
                if other_login_elements.count() > 0:
                    other_login_elements.first.click()
                    page.wait_for_timeout(1500)

                    if self.debug:
                        try:
                            page.screenshot(path="debug_after_other_login.png")
                            print("[Screenshot] 已保存截图: debug_after_other_login.png")
                        except PlaywrightError:
                            pass

                    print("[Lock] 查找密码登录方式（login-third-passwd）...")
                    passwd_login_span = page.locator("span.login-third-passwd")
                    if passwd_login_span.count() > 0:
                        page.evaluate("(el) => el.click()", passwd_login_span.first.element_handle())
                        print("[OK] 已点击密码登录图标")
                        page.wait_for_timeout(2500)

                        if self.debug:
                            try:
                                page.screenshot(path="debug_after_passwd_click.png")
                                print("[Screenshot] 已保存截图: debug_after_passwd_click.png")
                            except PlaywrightError:
                                pass
                    else:
                        print("  [WARN] 未找到密码登录元素，尝试继续...")
            except PlaywrightError as exc:
                print(f"[WARN] 未找到或点击其他登录方式失败: {str(exc)[:80]}")

            print("[Search] 查找用户名输入框...")
            try:
                username_input = page.wait_for_selector("input.base-input-text[autocomplete='username']", timeout=10000)
                print("[OK] 找到用户名输入框")
            except PlaywrightTimeoutError:
                print("[ERROR] 未找到用户名输入框")
                return False

            print("[Search] 查找密码输入框...")
            try:
                password_input = page.wait_for_selector("input.base-input-text[autocomplete='current-password']", timeout=10000)
                print("[OK] 找到密码输入框")
            except PlaywrightTimeoutError:
                print("[ERROR] 未找到密码输入框")
                return False

            print("[Input] 输入用户名和密码...")
            # 清空并输入用户名（加入人类输入延时）
            username_input.click()
            username_input.fill("")
            try:
                username_input.type(username, delay=random.randint(60, 120))
            except Exception:
                username_input.fill(username)
            print(f"  已输入用户名: {username}")
            page.wait_for_timeout(800)

            # 清空并输入密码（加入人类输入延时）
            password_input.click()
            password_input.fill("")
            try:
                password_input.type(password, delay=random.randint(60, 120))
            except Exception:
                password_input.fill(password)
            print(f"  已输入密码: {'*' * len(password)}")
            page.wait_for_timeout(800)

            if self.debug:
                try:
                    page.screenshot(path="debug_after_input.png")
                    print("[Screenshot] 已保存截图: debug_after_input.png")
                except PlaywrightError:
                    pass

            print("[Search] 查找登录按钮...")
            try:
                login_button = page.wait_for_selector("button.base-button", timeout=10000)
            except PlaywrightTimeoutError:
                print("[ERROR] 未找到登录按钮")
                return False

            print("[OK] 找到登录按钮")
            is_disabled = login_button.get_attribute("disabled")
            if is_disabled:
                print("[WARN] 登录按钮当前被禁用，等待启用...")
                page.wait_for_timeout(2000)
                is_disabled = login_button.get_attribute("disabled")
                if is_disabled:
                    print("  尝试通过JavaScript启用按钮...")
                    page.evaluate("(el) => el.removeAttribute('disabled')", login_button)
                    page.wait_for_timeout(500)

            print("[Click] 点击登录按钮...")
            try:
                login_button.click()
            except PlaywrightError:
                page.evaluate("(el) => el.click()", login_button)

            print("[Wait] 观察登录结果（最长20秒，轮询验证码/跳转）...")
            if self.debug:
                try:
                    page.screenshot(path="debug_after_login_click.png")
                    print("[Screenshot] 已保存截图: debug_after_login_click.png")
                except PlaywrightError:
                    pass

            # 轮询等待验证码或登录跳转，提高低网速下的稳定性
            captcha_selectors = [
                "xpath=//*[contains(text(), '安全验证')]",
                "xpath=//*[contains(text(), '请完成安全验证')]",
                ".caption__title",
                "#click_v2",
                ".verify-img-panel",
                "canvas",
                "img.geetest_item_img",
            ]

            captcha_triggered = False
            captcha_handled = False
            for i in range(20):
                try:
                    # 成功登录：URL 跳出 passport/login 即认为成功
                    if 'login' not in page.url and 'passport' not in page.url:
                        break

                    # 检测验证码出现
                    for selector in captcha_selectors:
                        locator = page.locator(selector)
                        if locator.count() > 0:
                            elem = locator.first
                            if elem.is_visible():
                                print(f"[Captcha] 检测到验证码元素: {selector}")
                                captcha_triggered = True
                                break
                    if captcha_triggered:
                        print("[Captcha] 检测到验证码！")
                        if self.use_captcha_service and self.captcha_service:
                            print("[Captcha] 调用自动识别服务...")
                            success = self._handle_captcha_auto()
                            if success:
                                print("[OK] 验证码自动识别完成！")
                                captcha_handled = True
                            else:
                                print("[ERROR] 自动识别失败，切换到手动模式")
                                self._handle_captcha_manual()
                        else:
                            print("[Captcha] 未启用验证码服务，进入手动模式")
                            self._handle_captcha_manual()
                        page.wait_for_timeout(2000)
                        break
                except PlaywrightError:
                    pass
                page.wait_for_timeout(1000)

            # 若验证码已处理，按需等待 3 秒让页面自然跳转，再继续判断是否仍在登录页
            try:
                if captcha_handled:
                    print("[Wait] 验证码通过，等待 3 秒以便页面跳转...")
                    page.wait_for_timeout(3000)
            except PlaywrightError:
                pass

            current_url = page.url
            print(f"[Location] 当前页面URL: {current_url}")

            try:
                error_messages = page.locator("xpath=//*[contains(@class, 'error') or contains(@class, 'tip')]")
                for idx in range(min(3, error_messages.count())):
                    elem = error_messages.nth(idx)
                    if elem.is_visible():
                        text = elem.inner_text().strip()
                        if text and '终于等到你' not in text:
                            print(f"[WARN] 页面提示: {text}")
                # 明确识别短信校验提示
                sms_locator = page.locator("xpath=//*[contains(text(), '发送短信进行安全验证') or contains(text(),'短信')]")
                if sms_locator.count() > 0 and sms_locator.first.is_visible():
                    print("[MFA] 需要短信验证，自动流程终止，请改为人工完成或复用持久化登录状态")
            except PlaywrightError:
                pass

            if 'login' not in current_url and 'passport' not in current_url:
                print("[OK] 登录成功！")
                if self.browser_context:
                    context_cookies = self.browser_context.cookies()
                    self.cookies = {item['name']: item['value'] for item in context_cookies}
                    print(f"[Note] 获取到 {len(self.cookies)} 个cookie")
                    self._save_cookies()
                return True

            print("[ERROR] 登录失败，仍在登录页面")
            return False

        except Exception as exc:
            print(f"[ERROR] 登录异常: {str(exc)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close()

    def load_cookies(self) -> bool:
        """
        从文件加载已保存的cookies

        Returns:
            bool: 是否成功加载cookies
        """
        if not os.path.exists(self.cookies_file):
            print(f"[WARN] cookies文件不存在: {self.cookies_file}")
            return False

        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                loaded_cookies = json.load(f)

            # 检查cookies是否为空
            if not loaded_cookies:
                print(f"[WARN] cookies文件为空，需要重新登录")
                return False

            # 检查cookies格式并转换
            if isinstance(loaded_cookies, list):
                # Playwright格式: [{"name": "xxx", "value": "yyy"}]
                self.cookies = {item['name']: item['value'] for item in loaded_cookies}
                print(f"[OK] 成功加载cookies (Playwright格式, {len(self.cookies)}个)")
            elif isinstance(loaded_cookies, dict):
                # 字典格式: {"name": "value"}
                self.cookies = loaded_cookies
                print(f"[OK] 成功加载cookies (字典格式, {len(self.cookies)}个)")
            else:
                print(f"[ERROR] cookies格式不正确: {type(loaded_cookies)}")
                return False

            # 检查关键cookies是否存在
            required_cookies = ['UserToken', 'UserInfo', 'UserName']
            missing_cookies = [cookie for cookie in required_cookies if cookie not in self.cookies]

            if missing_cookies:
                print(f"[WARN] 缺少关键cookies: {missing_cookies}，需要重新登录")
                return False

            return True

        except json.JSONDecodeError as e:
            print(f"[ERROR] cookies文件JSON格式错误: {str(e)}")
            return False
        except Exception as e:
            print(f"[ERROR] 加载cookies失败: {str(e)}")
            return False

    def _save_cookies(self):
        """保存cookies到文件"""
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(self.cookies, f, indent=2, ensure_ascii=False)
            print(f"[OK] Cookies已保存到 {self.cookies_file}")
        except Exception as e:
            print(f"[ERROR] 保存cookies失败: {str(e)}")

    def get_session(self):
        """获取已认证的session对象（使用requests）"""
        import requests
        session = requests.Session()

        # 设置User-Agent
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        })

        # 将cookies设置到session
        for name, value in self.cookies.items():
            session.cookies.set(name, value, domain='.csdn.net')

        return session

    def get_cookies(self) -> Dict[str, str]:
        """获取cookies字典"""
        return self.cookies

    def is_logged_in(self) -> bool:
        """
        检查是否已登录

        Returns:
            bool: 是否已登录
        """
        # 检查关键cookie是否存在
        required_cookies = ['UserToken', 'UserInfo', 'UserName']
        return all(cookie in self.cookies for cookie in required_cookies)

    def verify_login(self) -> bool:
        """
        验证登录状态是否有效

        Returns:
            bool: 登录状态是否有效
        """
        # 首先检查关键cookies是否存在
        if not self.is_logged_in():
            print("[ERROR] 缺少关键cookies，登录状态无效")
            return False

        try:
            # 使用requests验证登录状态
            session = self.get_session()
            test_url = "https://www.csdn.net/"

            print("[Search] 正在验证登录状态...")
            response = session.get(test_url, timeout=10)

            # 检查是否跳转到登录页
            if 'passport.csdn.net/login' in response.url:
                print("[ERROR] 登录状态已失效（跳转到登录页）")
                return False

            # 检查响应状态码
            if response.status_code != 200:
                print(f"[ERROR] 登录验证失败（状态码: {response.status_code}）")
                return False

            # 检查响应内容中是否包含用户信息
            # 优先检查是否有用户特定内容（更可靠）
            user_indicators = [
                '退出',
                '个人中心',
                '我的博客',
            ]

            # 如果有UserName，也检查用户名是否出现在页面中
            if 'UserName' in self.cookies and self.cookies['UserName']:
                user_indicators.append(self.cookies['UserName'])

            # 检查是否有任何用户特定内容
            has_user_content = any(indicator in response.text for indicator in user_indicators)

            if has_user_content:
                print("[OK] 登录状态有效（检测到用户特定内容）")
                return True

            # 如果没有用户特定内容，再检查是否显示登录按钮
            if '登录' in response.text and not has_user_content:
                print("[ERROR] 登录状态已失效（页面显示未登录）")
                return False

            # 默认情况：如果没有明确的登录标识，且没有重定向，认为已登录
            print("[OK] 登录状态有效（未检测到未登录标识）")
            return True

        except Exception as e:
            print(f"[ERROR] 验证登录状态异常: {str(e)}")
            return False

    def _handle_captcha_manual(self):
        """手动完成验证码"""
        print("[Pause]  请在浏览器窗口中手动完成验证码...")
        print("[Pause]  完成后程序将自动继续...")

        # 等待验证码完成（最多等待60秒）
        for i in range(60):
            time.sleep(1)
            if not self.page:
                break

            current_url = self.page.url

            # 检查是否已经跳转离开登录页
            if 'login' not in current_url and 'passport' not in current_url:
                print("[OK] 验证码已完成，登录成功！")
                return True

            # 检查验证码是否还在
            try:
                captcha_locator = self.page.locator("xpath=//*[contains(text(), '安全验证')]")
                visible = False
                for idx in range(captcha_locator.count()):
                    if captcha_locator.nth(idx).is_visible():
                        visible = True
                        break
                if not visible:
                    time.sleep(2)
                    return True
            except PlaywrightError:
                pass

        print("[WARN] 验证码等待超时")
        return False

    def _handle_captcha_auto(self) -> bool:
        """自动识别并完成验证码"""
        try:
            import tempfile
            import uuid
            if not self.page:
                print("[ERROR] 浏览器页面不可用，无法自动识别验证码")
                return False

            if not (self.use_captcha_service and self.captcha_service):
                print("[WARN] 未启用验证码服务，无法自动识别")
                return False

            # 查找验证码元素（CSDN使用canvas绘制，但需要截取完整的验证码区域）
            print("[Search] 查找验证码元素...")

            # 优先查找包含完整验证码的容器元素
            captcha_selectors = [
                ("#click_v2", "完整验证码容器"),  # CSDN验证码的完整容器（包含图片+文字提示）
                (".verify-img-panel", "验证码图片面板"),  # 验证码面板
                ("canvas", "Canvas元素"),  # 最后才尝试canvas
                ("img.geetest_item_img", "极验图片"),  # 极验类型
                ("img[class*='captcha']", "通用验证码图片")  # 通用验证码图片
            ]

            captcha_element = None
            element_type = ""
            for selector, name in captcha_selectors:
                locator = self.page.locator(selector)
                if locator.count() > 0:
                    elem = locator.first
                    if elem.is_visible():
                        captcha_element = elem
                        element_type = name
                        print(f"[OK] 找到验证码元素: {name} ({selector})")
                        break

            if not captcha_element:
                print("[ERROR] 未找到验证码元素")
                return False

            # 保存验证码图片（截取完整的验证码容器，包含图片和文字提示）
            # 解决 Permission denied: 在只读工作目录下改用可写的临时目录
            candidates = []
            # 1) 用户数据目录下的 tmp（一定可写，且会随会话清理）
            if self.user_data_dir and os.path.isdir(self.user_data_dir):
                candidates.append(os.path.join(self.user_data_dir, "tmp"))
            # 2) 系统临时目录
            candidates.append(tempfile.gettempdir())

            captcha_image_path = None
            filename = f"captcha_{uuid.uuid4().hex[:8]}.png"
            for base in candidates:
                try:
                    os.makedirs(base, exist_ok=True)
                    test_path = os.path.join(base, filename)
                    # 先尝试创建空文件以验证写权限
                    with open(test_path, 'wb') as _fh:
                        pass
                    os.remove(test_path)
                    captcha_image_path = os.path.join(base, filename)
                    break
                except Exception:
                    continue

            if not captcha_image_path:
                print("[ERROR] 无可写临时目录用于保存验证码截图")
                return False

            captcha_element.screenshot(path=captcha_image_path)
            print(f"[Screenshot] 已保存验证码图片到: {captcha_image_path}")

            # 调用验证码识别服务
            coordinates = self.captcha_service.recognize(captcha_image_path)

            if not coordinates:
                print("[ERROR] 验证码识别失败")
                return False

            print(f"[OK] 识别到 {len(coordinates)} 个坐标点")

            # 找到实际需要点击的canvas元素（在容器内部）
            # 因为我们截取的可能是完整容器，但点击要在canvas上
            click_target = None
            if element_type == "完整验证码容器":
                # 如果截取的是完整容器，需要找到里面的canvas来点击
                canvas_locator = self.page.locator("#click_v2 canvas, .verify-img-panel canvas")
                if canvas_locator.count() > 0:
                    click_target = canvas_locator.first
                    print("[Info] 使用容器内的canvas作为点击目标")

            # 如果没有找到canvas，就用原来的元素
            if not click_target:
                click_target = captcha_element

            # 获取点击目标在页面上的位置
            box = click_target.bounding_box()
            if not box:
                print("[ERROR] 无法获取验证码位置")
                return False

            # 点击识别到的坐标
            for i, (x, y) in enumerate(coordinates, 1):
                click_x = box["x"] + x
                click_y = box["y"] + y

                print(f"[Click]  点击第 {i} 个坐标: ({x}, {y})")
                self.page.mouse.move(click_x, click_y)
                self.page.mouse.click(click_x, click_y)
                time.sleep(0.5)

            # CSDN验证码点击完成后会自动提交，不需要点击确认按钮
            print("[Info] 验证码已点击完成，等待自动验证...")

            # 等待验证结果（给服务器时间验证）
            time.sleep(2)

            # 兜底：部分验证需要点击“确认/提交”按钮
            try:
                submit_candidates = [
                    "button:has-text(\"确认\")",
                    "button:has-text(\"验证\")",
                    "button:has-text(\"提交\")",
                    ".geetest_commit",
                    ".captcha-verify-submit",
                    "text=确认",
                    "text=验证",
                    "text=提交",
                    "text=完成",
                    "text=下一步",
                ]
                for sel in submit_candidates:
                    loc = self.page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        print(f"[Info] 尝试点击验证码提交按钮: {sel}")
                        try:
                            loc.first.click()
                        except PlaywrightError:
                            self.page.evaluate("(el) => el.click()", loc.first.element_handle())
                        time.sleep(1)
                        break
            except PlaywrightError:
                pass

            # 检查验证码是否消失或登录是否成功
            # 方法1: 检查是否跳转离开登录页
            current_url = self.page.url
            if 'login' not in current_url and 'passport' not in current_url:
                print("[OK] 验证码通过，已跳转")
                return True

            # 方法2: 检查验证码弹窗是否消失
            try:
                # 检查多个验证码相关元素
                captcha_elements = [
                    ".caption__title",
                    "xpath=//*[contains(text(), '安全验证')]",
                    ".verify-img-panel",
                    "canvas"
                ]

                all_disappeared = True
                for selector in captcha_elements:
                    locator = self.page.locator(selector)
                    if locator.count() > 0:
                        elem = locator.first
                        if elem.is_visible():
                            all_disappeared = False
                            break

                if all_disappeared:
                    print("[OK] 验证码弹窗已消失")
                    return True
                else:
                    print("[WARN] 验证码弹窗仍然可见，可能验证失败")
                    return False

            except PlaywrightError as e:
                print(f"[WARN] 检查验证码状态异常: {str(e)[:80]}")
                # 如果检查异常，保守起见返回False，让手动模式接管
                return False

        except Exception as e:
            print(f"[ERROR] 自动识别验证码异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _get_scan_output_dir(self):
        """获取扫码二维码保存目录，优先使用环境变量，然后尝试多个候选目录。

        Returns:
            str or None: 可写的目录路径，如果所有目录都不可写则返回 None
        """
        import tempfile

        # 输出目录优先级：env SCAN_OUTPUT_DIR -> tempfile.gettempdir()/scan -> /tmp/scan -> /app/pw_profile/scan -> tempfile.gettempdir()
        candidate_dirs = []
        env_scan_dir = os.getenv("SCAN_OUTPUT_DIR")
        if env_scan_dir:
            candidate_dirs.append(env_scan_dir)

        # 添加跨平台的临时目录
        temp_base = tempfile.gettempdir()
        candidate_dirs.append(os.path.join(temp_base, "scan"))

        # 添加传统Linux目录（用于向后兼容）
        candidate_dirs.extend(["/tmp/scan", "/app/pw_profile/scan", "/tmp"])

        # Windows 系统会使用上面的 tempfile.gettempdir()
        save_dir = None
        for d in candidate_dirs:
            try:
                os.makedirs(d, exist_ok=True)
                # 尝试写入测试文件验证权限
                test_name = os.path.join(d, ".scan_write_test")
                with open(test_name, "wb") as t:
                    t.write(b"ok")
                os.remove(test_name)
                save_dir = d
                break
            except Exception:
                continue

        return save_dir

    def _attempt_scan_login(self, wait_ms: int = 30000) -> bool:
        """微信扫码登录模式：抓取页面上的 data:image Base64 二维码并保存到 /tmp/scan。

        Args:
            wait_ms: 扫码等待时长（毫秒），默认 30 秒。

        Returns:
            bool: 扫码后是否已跳转离开登录页。
        """
        try:
            if not self.page:
                print("[ERROR] 页面不可用，无法执行扫码登录模式")
                return False

            page = self.page
            print("[Scan] 尝试进入微信扫码登录模式…")

            # 首先检查是否已经在微信扫码页面
            wechat_already_active = False
            try:
                # 检查是否有微信二维码容器
                wechat_containers = [
                    ".login-code-wechat",
                    ".public-code",
                    "#scan_box_applets"
                ]
                for sel in wechat_containers:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        wechat_already_active = True
                        print(f"[Scan] 已在微信扫码页面（检测到容器: {sel}）")
                        break
            except PlaywrightError:
                pass

            # 如果不在微信扫码页面，尝试切换
            if not wechat_already_active:
                print("[Scan] 尝试切换到微信扫码登录...")
                # 先把当前页面HTML保存下来，便于排查为何未展示扫码页
                try:
                    from datetime import datetime
                    save_dir = self._get_scan_output_dir()
                    if save_dir:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        html_path = os.path.join(save_dir, f"login_page_before_scan_{ts}.html")
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(page.content())
                        print(f"[Scan] 当前页面HTML已保存: {html_path}")
                except Exception as e:
                    print(f"[Scan] 保存当前页面HTML失败: {e}")

                # 步骤1: 展开"其他登录方式"
                try:
                    other_login = page.locator("text=其他登录方式")
                    if other_login.count() > 0 and other_login.first.is_visible():
                        print("[Scan] 点击'其他登录方式'")
                        other_login.first.click()
                        page.wait_for_timeout(1500)  # 增加等待时间
                    else:
                        print("[Scan] 未找到'其他登录方式'按钮，尝试继续...")
                except PlaywrightError as e:
                    print(f"[Scan] 点击'其他登录方式'失败: {str(e)[:80]}")

                # 步骤2: 点击微信登录图标/按钮
                wechat_clicked = False
                wechat_opts = [
                    ("text=微信扫码登录", "文本按钮"),
                    ("span.login-third-wechat", "图标span"),
                    (".login-third-wechat", "图标class"),
                    ("img[alt*='微信']", "微信图标"),
                    ("img[src*='wechat']", "微信图片"),
                ]

                for sel, desc in wechat_opts:
                    try:
                        loc = page.locator(sel)
                        if loc.count() > 0:
                            elem = loc.first
                            if elem.is_visible():
                                print(f"[Scan] 找到微信登录入口: {desc} ({sel})")
                                try:
                                    elem.click()
                                except PlaywrightError:
                                    # 使用JavaScript点击作为后备
                                    page.evaluate("(el)=>el.click()", elem.element_handle())

                                wechat_clicked = True
                                page.wait_for_timeout(2000)  # 等待二维码加载
                                print(f"[Scan] 已点击微信登录: {desc}")
                                break
                    except PlaywrightError as e:
                        print(f"[Scan] 尝试 {desc} 失败: {str(e)[:60]}")
                        continue

                if not wechat_clicked:
                    print("[WARN] 未能点击微信登录入口，可能页面结构已变化")

            # 现在查找二维码（增加更多选择器和重试）
            print("[Scan] 查找二维码...")

            selectors = [
                # base64格式的二维码
                ".login-code-wechat img[src^='data:']",
                ".public-code img[src^='data:']",
                "img[src^='data:image'][src*='base64']",
                # 远程URL的二维码
                ".login-code-wechat img[src*='qr']",
                ".public-code img",
                ".login-code-wechat canvas",  # 有些网站用canvas绘制二维码
                "img[alt*='二维码']",
                "img[alt*='扫码']",
            ]

            img_src = None

            # 增加等待时间到20秒，每秒检查一次；检测不到时尝试点击“二维码失效 点击重试”
            for attempt in range(20):
                for sel in selectors:
                    try:
                        loc = page.locator(sel)
                        if loc.count() > 0:
                            elem = loc.first
                            if elem.is_visible():
                                src = elem.get_attribute("src")
                                if src:
                                    img_src = src
                                    print(f"[Scan] 找到二维码: {sel}")
                                    break
                    except PlaywrightError:
                        continue

                if img_src:
                    break

                # 未找到二维码时，尝试点击“二维码失效 点击重试”入口刷新二维码
                try:
                    # 1) 精确匹配包含提示文本的标题
                    retry_title = page.locator("xpath=//span[contains(@class,'app-title') and contains(text(),'二维码失效')] | //span[contains(text(),'点击重试')]")
                    if retry_title.count() > 0 and retry_title.first.is_visible():
                        print("[Scan] 检测到二维码失效提示，尝试点击重试…")
                        try:
                            retry_title.first.click()
                        except PlaywrightError:
                            page.evaluate("(el)=>el.click()", retry_title.first.element_handle())
                        page.wait_for_timeout(1500)
                    else:
                        # 2) 点击容器或图标兜底
                        fail_container = page.locator(".app-fail")
                        icon_retry = page.locator(".app-fail .app-code-icon, .app-fail .huanyipi")
                        target = None
                        if icon_retry.count() > 0 and icon_retry.first.is_visible():
                            target = icon_retry.first
                        elif fail_container.count() > 0 and fail_container.first.is_visible():
                            target = fail_container.first
                        if target is not None:
                            print("[Scan] 点击二维码失败容器以刷新…")
                            try:
                                target.click()
                            except PlaywrightError:
                                page.evaluate("(el)=>el.click()", target.element_handle())
                            page.wait_for_timeout(1500)
                except PlaywrightError:
                    pass

                # 每5秒输出一次等待信息
                if attempt % 5 == 0 and attempt > 0:
                    print(f"[Scan] 仍在等待二维码出现... ({attempt}/20秒)")

                page.wait_for_timeout(1000)

            if not img_src:
                print("[ERROR] 未找到二维码图片，尝试截图整个页面...")
                # 作为兜底，截图整个登录区域
                try:
                    import tempfile
                    from datetime import datetime
                    save_dir = self._get_scan_output_dir()
                    if save_dir:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        fallback_path = os.path.join(save_dir, f"login_page_{ts}.png")
                        page.screenshot(path=fallback_path)
                        print(f"[Scan] 登录页面截图已保存: {fallback_path}")
                        print("[Scan] 请查看截图，如有二维码请手动扫描")
                except Exception as e:
                    print(f"[Scan] 截图失败: {e}")

                return False

            print(f"[Scan] 二维码类型: {'base64' if img_src.startswith('data:') else 'URL'}")

            # 解析并保存到扫描输出目录
            import base64
            import re
            from datetime import datetime

            header, _, b64data = img_src.partition(",")
            if not b64data:
                b64data = re.sub(r"^data:image/[^;]+;base64,", "", img_src)

            try:
                img_bytes = base64.b64decode(b64data)
            except Exception as e:
                print(f"[Scan] 解码二维码失败: {e}")
                return False

            # 推断扩展名
            ext = "png"
            if "jpeg" in header or "jpg" in header:
                ext = "jpg"
            elif "png" in header:
                ext = "png"

            # 获取可写的输出目录
            save_dir = self._get_scan_output_dir()
            if not save_dir:
                print("[Scan] 无可写目录用于保存二维码，请检查卷挂载/权限")
                return False

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(save_dir, f"wechat_qr_{ts}.{ext}")
            try:
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                print(f"[Scan] 二维码已保存: {file_path}")
                print("[Scan] 请使用微信扫描该二维码完成登录…")
            except Exception as e:
                print(f"[Scan] 保存二维码失败: {e}")
                return False

            # 如果后续页面结构不是 base64，而是远程图片，补充一个容器截图作为兜底
            try:
                container = None
                for sel in [".login-code-wechat .public-code", "#scan_box_applets", ".login-code-wechat"]:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        container = loc.first
                        break
                if container:
                    snap_path = os.path.join(save_dir, f"wechat_qr_container_{ts}.png")
                    container.screenshot(path=snap_path)
                    print(f"[Scan] 容器截图已保存: {snap_path}")
            except PlaywrightError:
                pass

            # 等待扫码确认
            try:
                page.wait_for_timeout(int(wait_ms))
            except Exception:
                time.sleep(wait_ms / 1000.0)

            cur = page.url
            if 'login' not in cur and 'passport' not in cur:
                print("[Scan] 扫码登录成功，已离开登录页")
                return True

            print("[Scan] 仍在登录页，可能未扫码或未确认")
            return False

        except Exception as e:
            print(f"[Scan] 扫码登录流程异常: {e}")
            return False

    def close(self):
        """关闭资源"""
        if self.browser_context:
            try:
                self.browser_context.close()
            except Exception as exc:
                print(f"[WARN] 关闭浏览器上下文失败: {exc}")
            finally:
                self.browser_context = None

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as exc:
                print(f"[WARN] 停止 Playwright 失败: {exc}")
            finally:
                self.playwright = None

        self.page = None
        self._cleanup_user_data_dir()
