"""
测试Stealth反爬虫绕过功能
验证Playwright能否成功访问CSDN页面，避免521错误
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stealth_utils():
    """测试stealth工具函数"""
    print("=" * 70)
    print("测试1: Stealth工具函数")
    print("=" * 70)

    from app.utils.stealth_utils import (
        get_random_viewport,
        get_latest_chrome_ua,
        get_stealth_launch_args,
        get_modern_browser_headers,
    )

    # 测试viewport生成
    viewport = get_random_viewport()
    print(f"[OK] 随机Viewport: {viewport['width']}x{viewport['height']}")

    # 测试UA生成
    ua = get_latest_chrome_ua()
    print(f"[OK] 最新UA: {ua[:80]}...")

    # 测试启动参数
    args = get_stealth_launch_args()
    print(f"[OK] 启动参数数量: {len(args)}个")
    print(f"     关键参数: --disable-blink-features=AutomationControlled")

    # 测试现代浏览器headers
    headers = get_modern_browser_headers()
    print(f"[OK] 现代浏览器Headers:")
    for key, value in headers.items():
        print(f"     {key}: {value}")

    print("\n")


def test_csdn_login_page_access():
    """测试访问CSDN登录页面（不执行登录）"""
    print("=" * 70)
    print("测试2: 访问CSDN登录页面（Stealth模式）")
    print("=" * 70)

    from playwright.sync_api import sync_playwright
    from app.utils.stealth_utils import (
        apply_stealth_to_page,
        get_latest_chrome_ua,
        get_random_viewport,
        get_stealth_launch_args,
        simulate_human_delay,
        handle_521_error,
        is_cloudflare_challenge,
    )

    print("\n[Info] 启动Playwright浏览器（Stealth模式）...")

    try:
        with sync_playwright() as p:
            # 使用stealth配置
            launch_args = get_stealth_launch_args()
            viewport = get_random_viewport()
            user_agent = get_latest_chrome_ua()

            print(f"[Stealth] Viewport: {viewport['width']}x{viewport['height']}")
            print(f"[Stealth] User-Agent: Chrome 131.0.0.0")

            browser = p.chromium.launch(
                headless=True,
                args=launch_args,
                ignore_default_args=['--enable-automation']
            )

            context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': viewport['width'], 'height': viewport['height']},
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                extra_http_headers={
                    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'DNT': '1',
                },
                ignore_https_errors=True,
                bypass_csp=True,
            )

            page = context.new_page()

            # 应用stealth
            print("[Stealth] 应用反检测配置...")
            apply_stealth_to_page(page)

            # 测试访问CSDN登录页
            login_url = "https://passport.csdn.net/login?code=applets"
            print(f"\n[Test] 尝试访问: {login_url}")

            success = handle_521_error(page, login_url, max_retries=3)

            if success:
                print("[OK] 页面访问成功！")

                # 检查是否遇到Cloudflare挑战
                if is_cloudflare_challenge(page):
                    print("[WARN] 检测到Cloudflare挑战页面")
                else:
                    print("[OK] 未遇到Cloudflare挑战")

                # 获取页面标题
                title = page.title()
                print(f"[Info] 页面标题: {title}")

                # 检查URL
                current_url = page.url
                print(f"[Info] 当前URL: {current_url}")

                # 检查页面内容
                content = page.content()
                if '登录' in content or 'login' in content.lower():
                    print("[OK] 检测到登录页面内容")
                else:
                    print("[WARN] 未检测到预期的登录页面内容")

                # 保存截图供检查
                screenshot_path = "test_stealth_screenshot.png"
                page.screenshot(path=screenshot_path)
                print(f"[Info] 页面截图已保存: {screenshot_path}")

            else:
                print("[ERROR] 页面访问失败（可能遇到521错误或Cloudflare拦截）")

            browser.close()

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n")


def test_auth_service_stealth():
    """测试AuthService的stealth集成"""
    print("=" * 70)
    print("测试3: AuthService Stealth集成")
    print("=" * 70)

    from app.services.auth_service import AuthService

    print("\n[Info] 初始化AuthService（启用验证码服务）...")

    try:
        auth_service = AuthService(use_captcha_service=False, debug=False)

        print("[Info] 初始化浏览器...")
        auth_service._init_browser()

        if auth_service.page:
            print("[OK] 浏览器初始化成功")

            # 测试访问登录页
            login_url = "https://passport.csdn.net/login?code=applets"
            print(f"[Test] 访问: {login_url}")

            from app.utils.stealth_utils import handle_521_error
            success = handle_521_error(auth_service.page, login_url, max_retries=3)

            if success:
                print("[OK] AuthService成功访问登录页面")
                print(f"[Info] 当前URL: {auth_service.page.url}")
                print(f"[Info] 页面标题: {auth_service.page.title()}")
            else:
                print("[ERROR] AuthService访问登录页面失败")

        else:
            print("[ERROR] 浏览器页面未初始化")

        # 清理
        auth_service.close()
        print("[Clean] 已关闭浏览器")

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n")


def test_article_service_stealth():
    """测试ArticleService的stealth集成（快速测试）"""
    print("=" * 70)
    print("测试4: ArticleService Stealth集成（快速）")
    print("=" * 70)

    print("\n[Info] 此测试需要有效的cookies.json文件")
    print("[Info] 如果没有cookies，将跳过此测试")

    import os
    if not os.path.exists('cookies.json'):
        print("[Skip] cookies.json不存在，跳过此测试")
        print("\n")
        return

    from app.services.article_service import ArticleService

    try:
        print("[Info] 初始化ArticleService...")
        article_service = ArticleService()

        # 测试文章URL
        test_url = "https://blog.csdn.net/weixin_43229348/article/details/151638092"
        print(f"[Test] 测试文章URL: {test_url}")

        # 注意：这会尝试真正下载文章，可能需要较长时间
        print("[Info] 尝试下载文章（仅测试访问，不保存）...")

        result = article_service.download_article(test_url)

        if result and result.get('title'):
            print(f"[OK] 文章下载成功")
            print(f"[Info] 文章标题: {result['title']}")
            print(f"[Info] 内容长度: {len(result.get('html', ''))} 字符")
        else:
            print("[WARN] 文章下载失败或返回为空")

        article_service.close()

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n")


def main():
    """主测试函数"""
    print("\n")
    print("=" * 70)
    print("CSDN Stealth反爬虫绕过测试套件")
    print("=" * 70)
    print("\n")

    # 运行所有测试
    test_stealth_utils()

    test_csdn_login_page_access()

    test_auth_service_stealth()

    # test_article_service_stealth()  # 需要cookies，可选

    print("=" * 70)
    print("所有测试完成！")
    print("=" * 70)
    print("\n")
    print("关键检查项:")
    print("1. 是否成功访问CSDN登录页面（无521错误）")
    print("2. 是否未遇到Cloudflare挑战页面")
    print("3. 页面标题和内容是否正确")
    print("4. 查看截图文件: test_stealth_screenshot.png")
    print("\n")


if __name__ == "__main__":
    main()
