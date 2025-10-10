import json
import os
import shutil
import time
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
        if self.user_data_dir and os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir)
                print(f"🧹 已清理旧的 user-data-dir: {self.user_data_dir}")
            except Exception as exc:
                print(f"⚠️ 清理 user-data-dir 失败: {exc}")
        self.user_data_dir = None

    def _init_captcha_service(self):
        """初始化验证码识别服务"""
        service_type = settings.CAPTCHA_SERVICE

        if service_type == 'chaojiying':
            return get_captcha_service(
                'chaojiying',
                username=settings.CHAOJIYING_USERNAME,
                password=settings.CHAOJIYING_PASSWORD,
                soft_id=settings.CHAOJIYING_SOFT_ID,
            )
        if service_type == '2captcha':
            return get_captcha_service(
                '2captcha',
                api_key=settings.TWOCAPTCHA_API_KEY,
            )
        if service_type == 'mock':
            return get_captcha_service('mock')

        print(f"⚠️ 未知的验证码服务类型: {service_type}，将使用手动模式")
        return None

    def _init_browser(self):
        """启动 Playwright Chromium 浏览器"""
        import tempfile

        # 先确保其它会话已经关闭
        self.close()

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            self._cleanup_user_data_dir()
            self.user_data_dir = tempfile.mkdtemp(prefix="pw_user_data_", dir="/tmp")

            try:
                self.playwright = sync_playwright().start()
                launch_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-sandbox",
                ]

                extra_args = os.getenv("PLAYWRIGHT_EXTRA_ARGS")
                if extra_args:
                    launch_args.extend(arg for arg in extra_args.split() if arg)

                headless = os.getenv("PLAYWRIGHT_HEADFUL", "0") != "1"

                context = self.playwright.chromium.launch_persistent_context(
                    self.user_data_dir,
                    headless=headless,
                    args=launch_args,
                    viewport={"width": 1280, "height": 720},
                    ignore_https_errors=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
                    bypass_csp=True,
                )

                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
                )

                self.browser_context = context
                self.page = context.pages[0] if context.pages else context.new_page()
                self.page.set_default_timeout(10000)

                print(f"✅ Chromium 启动成功 (尝试 {attempt}/{max_retries})")
                return
            except PlaywrightError as exc:
                print(f"❌ Chromium 启动失败 (尝试 {attempt}/{max_retries}): {str(exc)[:120]}")
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
                print("❌ 浏览器页面初始化失败")
                return False

            page = self.page

            print("📡 正在访问CSDN登录页面...")
            page.goto('https://passport.csdn.net/login?code=applets', wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            print("🔍 尝试切换到验证码登录模式...")
            try:
                verification_login_tab = page.locator("text=验证码登录")
                if verification_login_tab.count() > 0:
                    verification_login_tab.first.click()
                    page.wait_for_timeout(2000)
            except PlaywrightError as exc:
                print(f"  未找到验证码登录标签: {str(exc)[:80]}")

            print("🔍 查找其他登录方式...")
            try:
                other_login_elements = page.locator("text=其他登录方式")
                if other_login_elements.count() > 0:
                    other_login_elements.first.click()
                    page.wait_for_timeout(1500)

                    if self.debug:
                        try:
                            page.screenshot(path="debug_after_other_login.png")
                            print("📸 已保存截图: debug_after_other_login.png")
                        except PlaywrightError:
                            pass

                    print("🔒 查找密码登录方式（login-third-passwd）...")
                    passwd_login_span = page.locator("span.login-third-passwd")
                    if passwd_login_span.count() > 0:
                        page.evaluate("(el) => el.click()", passwd_login_span.first.element_handle())
                        print("✅ 已点击密码登录图标")
                        page.wait_for_timeout(2500)

                        if self.debug:
                            try:
                                page.screenshot(path="debug_after_passwd_click.png")
                                print("📸 已保存截图: debug_after_passwd_click.png")
                            except PlaywrightError:
                                pass
                    else:
                        print("  ⚠️ 未找到密码登录元素，尝试继续...")
            except PlaywrightError as exc:
                print(f"⚠️ 未找到或点击其他登录方式失败: {str(exc)[:80]}")

            print("🔍 查找用户名输入框...")
            try:
                username_input = page.wait_for_selector("input.base-input-text[autocomplete='username']", timeout=10000)
                print("✅ 找到用户名输入框")
            except PlaywrightTimeoutError:
                print("❌ 未找到用户名输入框")
                return False

            print("🔍 查找密码输入框...")
            try:
                password_input = page.wait_for_selector("input.base-input-text[autocomplete='current-password']", timeout=10000)
                print("✅ 找到密码输入框")
            except PlaywrightTimeoutError:
                print("❌ 未找到密码输入框")
                return False

            print("⌨️ 输入用户名和密码...")
            page.evaluate(
                """
                (el) => {
                    el.value = '';
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                username_input,
            )
            page.evaluate(
                """
                (el, value) => {
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                username_input,
                username,
            )
            print(f"  已输入用户名: {username}")
            page.wait_for_timeout(800)

            page.evaluate(
                """
                (el) => {
                    el.value = '';
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                password_input,
            )
            page.evaluate(
                """
                (el, value) => {
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                password_input,
                password,
            )
            print(f"  已输入密码: {'*' * len(password)}")
            page.wait_for_timeout(800)

            if self.debug:
                try:
                    page.screenshot(path="debug_after_input.png")
                    print("📸 已保存截图: debug_after_input.png")
                except PlaywrightError:
                    pass

            print("🔍 查找登录按钮...")
            try:
                login_button = page.wait_for_selector("button.base-button", timeout=10000)
            except PlaywrightTimeoutError:
                print("❌ 未找到登录按钮")
                return False

            print("✅ 找到登录按钮")
            is_disabled = login_button.get_attribute("disabled")
            if is_disabled:
                print("⚠️ 登录按钮当前被禁用，等待启用...")
                page.wait_for_timeout(2000)
                is_disabled = login_button.get_attribute("disabled")
                if is_disabled:
                    print("  尝试通过JavaScript启用按钮...")
                    page.evaluate("(el) => el.removeAttribute('disabled')", login_button)
                    page.wait_for_timeout(500)

            print("🖱️ 点击登录按钮...")
            try:
                login_button.click()
            except PlaywrightError:
                page.evaluate("(el) => el.click()", login_button)

            print("⏳ 等待登录结果...")
            page.wait_for_timeout(3000)

            if self.debug:
                try:
                    page.screenshot(path="debug_after_login_click.png")
                    print("📸 已保存截图: debug_after_login_click.png")
                except PlaywrightError:
                    pass

            try:
                captcha_locator = page.locator("xpath=//*[contains(text(), '安全验证') or contains(text(), '验证')]")
                captcha_visible = False
                for idx in range(captcha_locator.count()):
                    elem = captcha_locator.nth(idx)
                    if elem.is_visible():
                        captcha_visible = True
                        break

                if captcha_visible:
                    print("🔐 检测到验证码！")
                    if self.use_captcha_service and self.captcha_service:
                        success = self._handle_captcha_auto()
                        if success:
                            print("✅ 验证码自动识别完成！")
                        else:
                            print("❌ 自动识别失败，切换到手动模式")
                            self._handle_captcha_manual()
                    else:
                        self._handle_captcha_manual()
                    page.wait_for_timeout(2000)
            except PlaywrightError as exc:
                print(f"⚠️ 验证码处理异常: {str(exc)[:120]}")

            current_url = page.url
            print(f"📍 当前页面URL: {current_url}")

            try:
                error_messages = page.locator("xpath=//*[contains(@class, 'error') or contains(@class, 'tip')]")
                for idx in range(min(3, error_messages.count())):
                    elem = error_messages.nth(idx)
                    if elem.is_visible():
                        text = elem.inner_text().strip()
                        if text and '终于等到你' not in text:
                            print(f"⚠️ 页面提示: {text}")
            except PlaywrightError:
                pass

            if 'login' not in current_url and 'passport' not in current_url:
                print("✅ 登录成功！")
                if self.browser_context:
                    context_cookies = self.browser_context.cookies()
                    self.cookies = {item['name']: item['value'] for item in context_cookies}
                    print(f"📝 获取到 {len(self.cookies)} 个cookie")
                    self._save_cookies()
                return True

            print("❌ 登录失败，仍在登录页面")
            return False

        except Exception as exc:
            print(f"❌ 登录异常: {str(exc)}")
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
            return False

        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                self.cookies = json.load(f)

            print(f"✅ 成功加载cookies ({len(self.cookies)}个)")
            return True

        except Exception as e:
            print(f"❌ 加载cookies失败: {str(e)}")
            return False

    def _save_cookies(self):
        """保存cookies到文件"""
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(self.cookies, f, indent=2, ensure_ascii=False)
            print(f"✅ Cookies已保存到 {self.cookies_file}")
        except Exception as e:
            print(f"❌ 保存cookies失败: {str(e)}")

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
        try:
            # 使用requests验证登录状态
            session = self.get_session()
            test_url = "https://www.csdn.net/"
            response = session.get(test_url, timeout=10)

            # 如果能正常访问且没有跳转到登录页，说明登录有效
            if response.status_code == 200 and 'passport.csdn.net/login' not in response.url:
                print("✅ 登录状态有效")
                return True
            else:
                print("❌ 登录状态已失效")
                return False

        except Exception as e:
            print(f"❌ 验证登录状态异常: {str(e)}")
            return False

    def _handle_captcha_manual(self):
        """手动完成验证码"""
        print("⏸️  请在浏览器窗口中手动完成验证码...")
        print("⏸️  完成后程序将自动继续...")

        # 等待验证码完成（最多等待60秒）
        for i in range(60):
            time.sleep(1)
            if not self.page:
                break

            current_url = self.page.url

            # 检查是否已经跳转离开登录页
            if 'login' not in current_url and 'passport' not in current_url:
                print("✅ 验证码已完成，登录成功！")
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

        print("⚠️ 验证码等待超时")
        return False

    def _handle_captcha_auto(self) -> bool:
        """自动识别并完成验证码"""
        try:
            if not self.page:
                print("❌ 浏览器页面不可用，无法自动识别验证码")
                return False

            if not (self.use_captcha_service and self.captcha_service):
                print("⚠️ 未启用验证码服务，无法自动识别")
                return False

            # 查找验证码图片
            print("🔍 查找验证码图片...")
            captcha_locator = self.page.locator("img.geetest_item_img, img[class*='captcha']")
            if captcha_locator.count() == 0:
                print("❌ 未找到验证码图片")
                return False

            captcha_element = captcha_locator.first
            if not captcha_element.is_visible():
                print("❌ 验证码图片不可见")
                return False

            # 保存验证码图片
            captcha_image_path = "captcha_temp.png"
            captcha_element.screenshot(path=captcha_image_path)
            if self.debug:
                print(f"📸 已保存验证码图片: {captcha_image_path}")

            # 调用验证码识别服务
            coordinates = self.captcha_service.recognize(captcha_image_path)

            if not coordinates:
                print("❌ 验证码识别失败")
                return False

            print(f"✅ 识别到 {len(coordinates)} 个坐标点")

            # 获取图片在页面上的位置
            box = captcha_element.bounding_box()
            if not box:
                print("❌ 无法获取验证码位置")
                return False

            for i, (x, y) in enumerate(coordinates, 1):
                click_x = box["x"] + x
                click_y = box["y"] + y

                print(f"🖱️  点击第 {i} 个坐标: ({x}, {y})")
                self.page.mouse.move(click_x, click_y)
                self.page.mouse.click(click_x, click_y)
                time.sleep(0.5)

            # 查找并点击确认按钮
            try:
                confirm_button = self.page.locator("button[class*='confirm'], button:has-text('确认'), div[class*='commit']")
                if confirm_button.count() > 0:
                    confirm_button.first.click()
                    print("✅ 已点击确认按钮")
                else:
                    print("⚠️ 未找到确认按钮，验证码可能自动提交")
            except PlaywrightError:
                print("⚠️ 未找到确认按钮，验证码可能自动提交")

            # 等待验证结果
            time.sleep(3)

            # 检查验证码是否消失
            try:
                captcha_locator = self.page.locator("xpath=//*[contains(text(), '安全验证')]")
                visible = False
                for idx in range(captcha_locator.count()):
                    if captcha_locator.nth(idx).is_visible():
                        visible = True
                        break
                if not visible:
                    return True
            except PlaywrightError:
                pass

            return False

        except Exception as e:
            print(f"❌ 自动识别验证码异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def close(self):
        """关闭资源"""
        if self.browser_context:
            try:
                self.browser_context.close()
            except Exception as exc:
                print(f"⚠️ 关闭浏览器上下文失败: {exc}")
            finally:
                self.browser_context = None

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as exc:
                print(f"⚠️ 停止 Playwright 失败: {exc}")
            finally:
                self.playwright = None

        self.page = None
        self._cleanup_user_data_dir()
