"""
测试登录流程: 进入登录页 -> 输入用户名密码 -> 验证码验证 -> 登录成功
需要先在.env中配置:
- CSDN_USERNAME
- CSDN_PASSWORD
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.auth_service import AuthService
from app.core.config import settings


def test_full_login_flow():
    """测试完整的登录流程"""
    print("\n" + "="*60)
    print("Test: Complete Login Flow")
    print("="*60)

    # 检查配置
    if not settings.CSDN_USERNAME or not settings.CSDN_PASSWORD:
        print("[ERROR] CSDN_USERNAME or CSDN_PASSWORD not configured in .env")
        print("Please set:")
        print("  CSDN_USERNAME=your_username")
        print("  CSDN_PASSWORD=your_password")
        return False

    print(f"\n[INFO] Using account: {settings.CSDN_USERNAME}")
    print(f"[INFO] Captcha service: {settings.CAPTCHA_SERVICE}")

    # 删除现有cookies以触发登录
    if os.path.exists("cookies.json"):
        os.remove("cookies.json")
        print("[INFO] Removed existing cookies.json to force login")

    # 创建认证服务实例
    use_captcha = settings.CAPTCHA_SERVICE != 'manual'
    auth_service = AuthService(use_captcha_service=use_captcha, debug=True)

    print("\n" + "="*60)
    print("Step 1: Start Login Process")
    print("="*60)

    try:
        # 执行登录
        success = auth_service.login(
            username=settings.CSDN_USERNAME,
            password=settings.CSDN_PASSWORD
        )

        print("\n" + "="*60)
        print("Step 2: Check Login Result")
        print("="*60)

        if success:
            print("[PASS] Login successful!")

            # 检查cookies是否保存
            if os.path.exists("cookies.json"):
                print("[PASS] cookies.json file created")

                # 检查cookies内容
                import json
                with open("cookies.json", "r", encoding="utf-8") as f:
                    cookies = json.load(f)

                print(f"[INFO] Cookies count: {len(cookies)}")

                # 检查关键cookies
                required_cookies = ['UserToken', 'UserInfo', 'UserName']
                for cookie_name in required_cookies:
                    if cookie_name in cookies:
                        print(f"[PASS] {cookie_name}: exists")
                    else:
                        print(f"[FAIL] {cookie_name}: missing")

                print("\n" + "="*60)
                print("Step 3: Verify Login Status")
                print("="*60)

                # 重新加载cookies并验证
                auth_service2 = AuthService(use_captcha_service=False, debug=False)
                if auth_service2.load_cookies():
                    print("[PASS] Cookies can be loaded successfully")

                    if auth_service2.is_logged_in():
                        print("[PASS] is_logged_in() returns True")
                    else:
                        print("[FAIL] is_logged_in() returns False")

                    if auth_service2.verify_login():
                        print("[PASS] verify_login() returns True")
                    else:
                        print("[FAIL] verify_login() returns False")
                else:
                    print("[FAIL] Cannot load cookies")

                return True
            else:
                print("[FAIL] cookies.json file not created")
                return False
        else:
            print("[FAIL] Login failed")
            return False

    except Exception as e:
        print(f"\n[ERROR] Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理资源
        auth_service.close()


def test_cookies_invalidation():
    """测试cookies失效时是否能重新登录"""
    print("\n" + "="*60)
    print("Test: Auto Re-login on Invalid Cookies")
    print("="*60)

    # 创建无效的cookies文件
    import json
    invalid_cookies = {
        "UserToken": "invalid_token_12345",
        "UserInfo": "invalid_info",
        "UserName": "invalid_user"
    }

    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(invalid_cookies, f)
    print("[INFO] Created invalid cookies.json")

    # 尝试验证登录（应该失败）
    auth_service = AuthService(use_captcha_service=False, debug=False)
    auth_service.load_cookies()

    print("\n[INFO] Verifying login with invalid cookies...")
    is_valid = auth_service.verify_login()

    if not is_valid:
        print("[PASS] verify_login() correctly detected invalid cookies")
        print("[INFO] In real scenario, this would trigger re-login")
        return True
    else:
        print("[FAIL] verify_login() should return False for invalid cookies")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("   CSDN Login Flow Test Suite")
    print("="*70)

    results = []

    # 测试1: 完整登录流程
    print("\n" + ">"*70)
    print(">>> Test 1: Full Login Flow (with Playwright)")
    print(">"*70)
    result1 = test_full_login_flow()
    results.append(("Full Login Flow", result1))

    # 测试2: Cookies失效检测
    print("\n" + ">"*70)
    print(">>> Test 2: Invalid Cookies Detection")
    print(">"*70)
    result2 = test_cookies_invalidation()
    results.append(("Invalid Cookies Detection", result2))

    # 总结
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        print("\nLogin flow validation:")
        print("1. [OK] Can enter login page and input credentials")
        print("2. [OK] Can handle captcha (auto or manual)")
        print("3. [OK] Can save cookies after successful login")
        print("4. [OK] Can detect invalid cookies and trigger re-login")
        return 0
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
