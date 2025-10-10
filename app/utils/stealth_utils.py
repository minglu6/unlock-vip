"""
Playwright Stealth工具模块 - 绕过反爬虫检测

提供浏览器指纹伪装、人类行为模拟、反检测配置等功能
"""
import random
import time
from typing import Optional, Dict, Any
from playwright.sync_api import Page, BrowserContext
from playwright_stealth.stealth import Stealth

# 创建全局Stealth实例
_stealth_instance = Stealth()


def get_random_viewport() -> Dict[str, int]:
    """
    获取随机的viewport尺寸，模拟不同用户的屏幕分辨率

    Returns:
        dict: 包含width和height的字典
    """
    common_viewports = [
        {"width": 1920, "height": 1080},  # Full HD
        {"width": 1366, "height": 768},   # 常见笔记本
        {"width": 1536, "height": 864},   # Windows缩放125%
        {"width": 1440, "height": 900},   # MacBook
        {"width": 2560, "height": 1440},  # 2K
        {"width": 1280, "height": 720},   # HD
    ]
    return random.choice(common_viewports)


def get_latest_chrome_ua() -> str:
    """
    获取最新版本的Chrome User-Agent (2025年1月)

    Returns:
        str: User-Agent字符串
    """
    # Chrome 131.0.0.0 - 2025年1月最新版本
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def get_modern_browser_headers() -> Dict[str, str]:
    """
    获取现代浏览器的完整请求头

    Returns:
        dict: 请求头字典
    """
    return {
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'DNT': '1',
    }


def get_stealth_launch_args() -> list:
    """
    获取Playwright启动参数，隐藏自动化特征

    Returns:
        list: 启动参数列表
    """
    return [
        # 核心反检测参数
        "--disable-blink-features=AutomationControlled",

        # 性能优化参数
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--no-sandbox",

        # 额外的反检测参数
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--disable-web-security",
        "--disable-blink-features",
        "--disable-infobars",

        # 模拟真实浏览器
        "--window-size=1920,1080",
        "--start-maximized",
    ]


def apply_stealth_to_page(page: Page) -> None:
    """
    对Playwright页面应用stealth配置，隐藏自动化特征

    Args:
        page: Playwright页面对象
    """
    # 应用playwright-stealth插件
    _stealth_instance.apply_stealth_sync(page)

    # 额外的JavaScript注入，进一步隐藏自动化特征
    page.add_init_script("""
        // 隐藏webdriver属性
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // 覆盖permissions查询（避免通知权限检测）
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // 修复Chrome对象（模拟真实Chrome）
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // 隐藏Playwright特有的属性
        delete navigator.__proto__.webdriver;

        // 模拟真实的插件列表
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: ""},
                    description: "",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                    1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                    description: "",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ]
        });

        // 模拟真实的语言列表
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
    """)


def apply_stealth_to_context(context: BrowserContext) -> None:
    """
    对Playwright上下文应用stealth配置

    Args:
        context: Playwright浏览器上下文对象
    """
    # 为上下文中的所有页面应用stealth
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)


def simulate_human_delay(min_ms: int = 500, max_ms: int = 2000) -> None:
    """
    模拟人类操作延迟

    Args:
        min_ms: 最小延迟毫秒数
        max_ms: 最大延迟毫秒数
    """
    delay = random.uniform(min_ms, max_ms) / 1000.0
    time.sleep(delay)


def simulate_mouse_movement(page: Page) -> None:
    """
    模拟鼠标随机移动，增加真实性

    Args:
        page: Playwright页面对象
    """
    try:
        # 获取viewport尺寸
        viewport = page.viewport_size
        if viewport:
            width = viewport['width']
            height = viewport['height']

            # 随机移动鼠标2-4次
            moves = random.randint(2, 4)
            for _ in range(moves):
                x = random.randint(50, width - 50)
                y = random.randint(50, height - 50)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
    except Exception:
        # 如果移动失败，忽略错误
        pass


def simulate_scroll(page: Page) -> None:
    """
    模拟页面滚动，增加真实性

    Args:
        page: Playwright页面对象
    """
    try:
        # 随机滚动1-3次
        scrolls = random.randint(1, 3)
        for _ in range(scrolls):
            scroll_amount = random.randint(100, 500)
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.2, 0.5))
    except Exception:
        # 如果滚动失败，忽略错误
        pass


def is_cloudflare_challenge(page: Page) -> bool:
    """
    检测页面是否为Cloudflare挑战页面

    Args:
        page: Playwright页面对象

    Returns:
        bool: 是否为Cloudflare挑战页面
    """
    try:
        content = page.content().lower()

        # Cloudflare挑战页面的特征
        cloudflare_indicators = [
            'cloudflare',
            'checking your browser',
            'just a moment',
            'please wait',
            'cdn-cgi/challenge-platform',
            'cf-browser-verification',
        ]

        return any(indicator in content for indicator in cloudflare_indicators)
    except Exception:
        return False


def wait_for_cloudflare_clearance(page: Page, timeout_ms: int = 30000) -> bool:
    """
    等待Cloudflare验证通过

    Args:
        page: Playwright页面对象
        timeout_ms: 超时时间（毫秒）

    Returns:
        bool: 是否成功通过验证
    """
    import time

    print("[Stealth] 检测到Cloudflare验证，等待通过...")

    start_time = time.time()
    timeout_sec = timeout_ms / 1000.0

    while time.time() - start_time < timeout_sec:
        if not is_cloudflare_challenge(page):
            print("[Stealth] Cloudflare验证已通过")
            return True

        # 每秒检查一次
        time.sleep(1)

    print("[Stealth] Cloudflare验证超时")
    return False


def handle_521_error(page: Page, url: str, max_retries: int = 3) -> bool:
    """
    处理521错误（Web服务器宕机 / Cloudflare保护）

    Args:
        page: Playwright页面对象
        url: 目标URL
        max_retries: 最大重试次数

    Returns:
        bool: 是否成功访问
    """
    for attempt in range(1, max_retries + 1):
        print(f"[Stealth] 尝试访问 (第{attempt}/{max_retries}次)...")

        try:
            # 访问页面
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # 检查响应状态
            if response and response.status == 521:
                print(f"[ERROR] 收到521错误，等待{2 ** attempt}秒后重试...")
                time.sleep(2 ** attempt)  # 指数退避
                continue

            # 检查是否为Cloudflare挑战
            if is_cloudflare_challenge(page):
                if wait_for_cloudflare_clearance(page):
                    return True
                else:
                    print(f"[ERROR] Cloudflare验证失败，等待{2 ** attempt}秒后重试...")
                    time.sleep(2 ** attempt)
                    continue

            # 成功访问
            print("[Stealth] 页面访问成功")
            return True

        except Exception as e:
            print(f"[ERROR] 访问失败: {str(e)}")
            if attempt < max_retries:
                print(f"[Stealth] 等待{2 ** attempt}秒后重试...")
                time.sleep(2 ** attempt)

    print("[ERROR] 达到最大重试次数，访问失败")
    return False


def create_stealth_context_options(headless: bool = True) -> Dict[str, Any]:
    """
    创建带有stealth配置的Playwright上下文选项

    Args:
        headless: 是否使用无头模式

    Returns:
        dict: 上下文配置选项
    """
    viewport = get_random_viewport()
    ua = get_latest_chrome_ua()
    headers = get_modern_browser_headers()

    return {
        'viewport': viewport,
        'user_agent': ua,
        'locale': 'zh-CN',
        'timezone_id': 'Asia/Shanghai',
        'ignore_https_errors': True,
        'bypass_csp': True,
        'extra_http_headers': headers,
        'java_script_enabled': True,
        'accept_downloads': False,
        'has_touch': False,
        'is_mobile': False,
    }


def create_stealth_launch_options(headless: bool = True) -> Dict[str, Any]:
    """
    创建带有stealth配置的Playwright启动选项

    Args:
        headless: 是否使用无头模式

    Returns:
        dict: 启动配置选项
    """
    return {
        'headless': headless,
        'args': get_stealth_launch_args(),
        'ignore_default_args': ['--enable-automation'],
        'channel': None,  # 使用下载的Chromium
    }
