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
                print(f"[Clean] 已清理旧的 user-data-dir: {self.user_data_dir}")
            except Exception as exc:
                print(f"[WARN] 清理 user-data-dir 失败: {exc}")
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
            # 使用系统默认临时目录，跨平台兼容（Windows/Linux/Mac）
            self.user_data_dir = tempfile.mkdtemp(prefix="pw_user_data_")

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
            page.goto('https://passport.csdn.net/login?code=applets', wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

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
            # 清空并输入用户名
            username_input.click()
            username_input.fill("")  # 清空
            username_input.fill(username)  # 输入
            print(f"  已输入用户名: {username}")
            page.wait_for_timeout(800)

            # 清空并输入密码
            password_input.click()
            password_input.fill("")  # 清空
            password_input.fill(password)  # 输入
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

            print("[Wait] 等待登录结果...")
            page.wait_for_timeout(3000)

            if self.debug:
                try:
                    page.screenshot(path="debug_after_login_click.png")
                    print("[Screenshot] 已保存截图: debug_after_login_click.png")
                except PlaywrightError:
                    pass

            try:
                # 检测多种验证码标识
                captcha_selectors = [
                    "xpath=//*[contains(text(), '安全验证')]",
                    "xpath=//*[contains(text(), '请完成安全验证')]",
                    ".caption__title",  # CSDN验证码标题
                    "canvas",  # CSDN使用canvas
                    ".verify-img-panel"  # 验证码面板
                ]

                captcha_visible = False
                for selector in captcha_selectors:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        elem = locator.first
                        if elem.is_visible():
                            captcha_visible = True
                            print(f"[Captcha] 检测到验证码元素: {selector}")
                            break

                if captcha_visible:
                    print("[Captcha] 检测到验证码！")
                    if self.use_captcha_service and self.captcha_service:
                        success = self._handle_captcha_auto()
                        if success:
                            print("[OK] 验证码自动识别完成！")
                        else:
                            print("[ERROR] 自动识别失败，切换到手动模式")
                            self._handle_captcha_manual()
                    else:
                        self._handle_captcha_manual()
                    page.wait_for_timeout(2000)
            except PlaywrightError as exc:
                print(f"[WARN] 验证码处理异常: {str(exc)[:120]}")

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
            if '登录' in response.text and '退出' not in response.text:
                print("[ERROR] 登录状态已失效（页面显示未登录）")
                return False

            print("[OK] 登录状态有效")
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
            captcha_image_path = "captcha_temp.png"
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
            time.sleep(3)

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
