"""
详细测试 verify_login 方法
检查响应内容以确定失败原因
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth_service import AuthService


def test_verify_login_detail():
    """详细测试verify_login方法"""
    print("="*70)
    print("Detailed verify_login Test")
    print("="*70)

    if not os.path.exists("cookies.json"):
        print("\n[ERROR] cookies.json not found!")
        return False

    # 创建AuthService并加载cookies
    print("\n[Step 1] Loading cookies...")
    auth_service = AuthService(use_captcha_service=False, debug=False)

    if not auth_service.load_cookies():
        print("  [FAIL] Failed to load cookies")
        return False

    print(f"  [OK] Loaded {len(auth_service.cookies)} cookies")

    # 检查关键cookies
    print("\n[Step 2] Checking required cookies...")
    required = ['UserToken', 'UserInfo', 'UserName']
    for key in required:
        if key in auth_service.cookies:
            value = auth_service.cookies[key]
            preview = value[:20] + "..." if len(value) > 20 else value
            print(f"  [OK] {key}: {preview}")
        else:
            print(f"  [MISS] {key}: NOT FOUND")

    # 检查is_logged_in
    print("\n[Step 3] Testing is_logged_in()...")
    if auth_service.is_logged_in():
        print("  [OK] is_logged_in() = True")
    else:
        print("  [FAIL] is_logged_in() = False")
        return False

    # 手动测试HTTP请求
    print("\n[Step 4] Manual HTTP request test...")
    print("  Making request to https://www.csdn.net/")

    try:
        import requests
        session = auth_service.get_session()

        response = session.get("https://www.csdn.net/", timeout=10)

        print(f"  Status code: {response.status_code}")
        print(f"  Final URL: {response.url}")
        print(f"  Response length: {len(response.text)} bytes")

        # 检查重定向
        if 'passport.csdn.net/login' in response.url:
            print("  [FAIL] Redirected to login page")
            print("  Cookies are invalid or expired")
            return False
        else:
            print("  [OK] No redirect to login page")

        # 检查响应内容
        print("\n[Step 5] Checking response content...")

        # 检查是否包含登录相关的文本
        content_checks = [
            ('登录', '登录' in response.text),
            ('退出', '退出' in response.text),
            ('个人中心', '个人中心' in response.text),
            ('我的博客', '我的博客' in response.text),
        ]

        for text, found in content_checks:
            status = "[FOUND]" if found else "[NOT FOUND]"
            print(f"  {status} '{text}'")

        # 判断登录状态
        print("\n[Step 6] Determining login status...")

        if '登录' in response.text and '退出' not in response.text:
            print("  [FAIL] Page shows '登录' but no '退出'")
            print("  This indicates NOT logged in")
            return False
        elif '退出' in response.text or '个人中心' in response.text:
            print("  [OK] Page shows '退出' or '个人中心'")
            print("  This indicates logged in")
            return True
        else:
            print("  [UNCERTAIN] Cannot determine from content")
            print("  Assuming logged in (no redirect)")
            return True

    except Exception as e:
        print(f"  [ERROR] Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "*"*70)
    print("  verify_login() Detailed Test")
    print("*"*70)

    result = test_verify_login_detail()

    print("\n" + "="*70)
    print("Final Result")
    print("="*70)

    if result:
        print("  [SUCCESS] Cookies are valid, login status is active")
        return 0
    else:
        print("  [FAILED] Cookies are invalid or expired")
        print("\n  Possible reasons:")
        print("    1. Cookies have expired (session timeout)")
        print("    2. CSDN logged out the session")
        print("    3. IP address changed (if CSDN checks IP)")
        print("\n  Solution:")
        print("    Run login again to get fresh cookies")
        print("    Example: python test_login_simple.py")
        return 1


if __name__ == "__main__":
    exit(main())
