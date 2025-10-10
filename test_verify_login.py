"""
测试 verify_login 方法
使用当前保存的 cookies.json 验证登录状态是否有效
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth_service import AuthService


def test_verify_login_with_saved_cookies():
    """测试使用保存的cookies验证登录状态"""
    print("="*70)
    print("Test: verify_login with saved cookies.json")
    print("="*70)

    # 检查cookies文件是否存在
    if not os.path.exists("cookies.json"):
        print("\n[ERROR] cookies.json not found!")
        print("Please run login first to generate cookies.json")
        return False

    # 显示cookies信息
    print("\n[Step 1] Loading cookies.json...")
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies_data = json.load(f)

    print(f"  Cookies count: {len(cookies_data)}")
    print(f"  Cookies type: {type(cookies_data)}")

    # 检查关键cookies
    required_cookies = ['UserToken', 'UserInfo', 'UserName']
    if isinstance(cookies_data, dict):
        for cookie_name in required_cookies:
            exists = "YES" if cookie_name in cookies_data else "NO"
            if exists == "YES":
                value_preview = cookies_data[cookie_name][:20] + "..." if len(cookies_data[cookie_name]) > 20 else cookies_data[cookie_name]
                print(f"  {cookie_name}: {exists} ({value_preview})")
            else:
                print(f"  {cookie_name}: {exists}")

    # 创建AuthService实例
    print("\n[Step 2] Creating AuthService instance...")
    auth_service = AuthService(use_captcha_service=False, debug=False)

    # 加载cookies
    print("\n[Step 3] Loading cookies with load_cookies()...")
    load_result = auth_service.load_cookies()

    if load_result:
        print("  [OK] Cookies loaded successfully")
        print(f"  Loaded cookies count: {len(auth_service.cookies)}")
    else:
        print("  [FAIL] Failed to load cookies")
        return False

    # 检查 is_logged_in
    print("\n[Step 4] Checking is_logged_in()...")
    is_logged_in = auth_service.is_logged_in()

    if is_logged_in:
        print("  [OK] is_logged_in() returned True")
        print("  All required cookies are present")
    else:
        print("  [FAIL] is_logged_in() returned False")
        print("  Missing required cookies")
        return False

    # 验证登录状态
    print("\n[Step 5] Verifying login status with verify_login()...")
    print("  This will make HTTP request to https://www.csdn.net/")
    print("  Please wait...")

    verify_result = auth_service.verify_login()

    print(f"\n{'='*70}")
    print("Test Result")
    print(f"{'='*70}")

    if verify_result:
        print("  [SUCCESS] verify_login() returned True")
        print("  Login status is VALID")
        print("  Cookies are working correctly")
        return True
    else:
        print("  [FAILED] verify_login() returned False")
        print("  Login status is INVALID")
        print("  Cookies may have expired or are invalid")
        return False


def test_verify_login_scenarios():
    """测试多种场景"""
    print("\n" + "="*70)
    print("Running Multiple Test Scenarios")
    print("="*70)

    scenarios = []

    # 场景1: 使用保存的cookies
    print("\n[Scenario 1] Using saved cookies.json")
    result1 = test_verify_login_with_saved_cookies()
    scenarios.append(("Saved cookies", result1))

    # 场景2: 测试空cookies
    print("\n" + "="*70)
    print("[Scenario 2] Testing with empty cookies")
    print("="*70)
    auth_service = AuthService(use_captcha_service=False, debug=False)
    auth_service.cookies = {}
    result2 = auth_service.is_logged_in()
    print(f"  is_logged_in() with empty cookies: {result2}")
    scenarios.append(("Empty cookies", not result2))  # Should be False

    # 场景3: 测试缺少关键cookies
    print("\n" + "="*70)
    print("[Scenario 3] Testing with missing required cookies")
    print("="*70)
    auth_service = AuthService(use_captcha_service=False, debug=False)
    auth_service.cookies = {"UserToken": "test"}  # 缺少 UserInfo 和 UserName
    result3 = auth_service.is_logged_in()
    print(f"  is_logged_in() with incomplete cookies: {result3}")
    scenarios.append(("Incomplete cookies", not result3))  # Should be False

    # 场景4: 测试所有关键cookies都存在
    print("\n" + "="*70)
    print("[Scenario 4] Testing with all required cookies present")
    print("="*70)
    auth_service = AuthService(use_captcha_service=False, debug=False)
    auth_service.cookies = {
        "UserToken": "test_token",
        "UserInfo": "test_info",
        "UserName": "test_name"
    }
    result4 = auth_service.is_logged_in()
    print(f"  is_logged_in() with all required cookies: {result4}")
    scenarios.append(("All required cookies", result4))  # Should be True

    # 总结
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)

    passed = 0
    failed = 0

    for scenario, result in scenarios:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {scenario}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n  Total: {len(scenarios)} tests")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed == 0:
        print("\n  [SUCCESS] All tests passed!")
        return True
    else:
        print(f"\n  [FAILED] {failed} test(s) failed")
        return False


def main():
    """运行测试"""
    print("\n" + "*"*70)
    print("  verify_login() Method Test Suite")
    print("*"*70)

    try:
        success = test_verify_login_scenarios()

        print("\n" + "="*70)
        if success:
            print("  All tests completed successfully!")
        else:
            print("  Some tests failed!")
        print("="*70)

        return 0 if success else 1

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
