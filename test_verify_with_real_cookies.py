"""
使用真实的cookies测试 verify_login 方法
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth_service import AuthService


def parse_cookie_string(cookie_string):
    """
    解析Cookie字符串为字典
    格式: name1=value1; name2=value2; ...
    """
    cookies = {}

    # 分割每个cookie
    cookie_pairs = cookie_string.split('; ')

    for pair in cookie_pairs:
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookies[name.strip()] = value.strip()

    return cookies


def test_with_real_cookies():
    """使用真实cookies测试"""
    print("="*70)
    print("Test verify_login with Real Cookies")
    print("="*70)

    # 真实的Cookie字符串
    cookie_string = """uuid_tt_dd=10_37073029060-1744764649384-303632; fid=20_15857838147-1744764651083-624090; Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac=1756454268,1756794401,1756872706,1758008490; _clck=z6powj%5E2%5Efzg%5E0%5E1932; c_ab_test=1; csdn_newcert_weixin_42273662=1; csdn_newcert_ForagerNet=1; c_adb=1; UN=weixin_42273662; p_uid=U110000; c_segment=0; dc_sid=8e6fec4bf4250baabf2365000343ad95; creative_btn_mp=3; loginbox_strategy=%7B%22blog-threeH-dialog-exp11tipShowTimes%22%3A2%2C%22blog-threeH-dialog-exp11%22%3A%22%22%2C%22taskId%22%3A317%2C%22abCheckTime%22%3A1760090145808%2C%22version%22%3A%22ExpA%22%2C%22nickName%22%3A%22InternetHerder%22%2C%22blog-threeH-dialog-expa%22%3A1759194998941%7D; c_first_page=https%3A//passport.csdn.net/login%3Fcode%3Dapplets; c_first_ref=default; dc_session_id=10_1760094486089.436866; c_dsid=11_1760094486868.083569; hide_login=1; c-sidebar-collapse=0; c_utm_medium=distribute.pc_feed_vip_blog_category.none-task-blog-classify_tag-1-151814724-null-null.nonecase; SESSION=e4118eaa-02b0-4e5d-8187-bfc0f3759bde; UserName=weixin_42273662; UserInfo=ac830d3a4e4e4bdc912ec5c8b372b1d8; UserToken=ac830d3a4e4e4bdc912ec5c8b372b1d8; UserNick=InternetHerder; AU=2DC; BT=1760094685893; c_pref=https%3A//blog.csdn.net/%3Fspm%3D1001.2101.3001.4477; c_ref=https%3A//blog.csdn.net/weixin_42273662%3Ftype%3Dblog; log_Id_click=13; c_page_id=default; log_Id_pv=9; log_Id_view=367; dc_tos=t3wy3s"""

    # 解析cookies
    print("\n[Step 1] Parsing cookie string...")
    cookies = parse_cookie_string(cookie_string)
    print(f"  Total cookies parsed: {len(cookies)}")

    # 显示关键cookies
    print("\n[Step 2] Checking key cookies...")
    key_cookies = ['UserToken', 'UserInfo', 'UserName', 'SESSION']
    for key in key_cookies:
        if key in cookies:
            value = cookies[key]
            preview = value[:30] + "..." if len(value) > 30 else value
            print(f"  [OK] {key}: {preview}")
        else:
            print(f"  [MISS] {key}: NOT FOUND")

    # 保存到临时文件用于测试
    print("\n[Step 3] Saving cookies to test_cookies_real.json...")
    test_cookie_file = "test_cookies_real.json"
    with open(test_cookie_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Saved to {test_cookie_file}")

    # 创建AuthService实例并加载cookies
    print("\n[Step 4] Creating AuthService and loading cookies...")
    auth_service = AuthService(use_captcha_service=False, debug=False)
    auth_service.cookies = cookies
    print(f"  [OK] Loaded {len(auth_service.cookies)} cookies into AuthService")

    # 测试 is_logged_in
    print("\n[Step 5] Testing is_logged_in()...")
    is_logged = auth_service.is_logged_in()
    print(f"  Result: {is_logged}")

    if is_logged:
        print("  [OK] All required cookies present")
    else:
        print("  [FAIL] Missing required cookies")
        missing = []
        required = ['UserToken', 'UserInfo', 'UserName']
        for req in required:
            if req not in cookies:
                missing.append(req)
        if missing:
            print(f"  Missing: {missing}")

    # 测试 verify_login
    print("\n[Step 6] Testing verify_login()...")
    print("  Making HTTP request to https://www.csdn.net/")
    print("  This will check if cookies are valid on server...")

    verify_result = auth_service.verify_login()

    print(f"\n{'='*70}")
    print("Test Results")
    print(f"{'='*70}")

    print(f"\n1. Cookie Parsing: SUCCESS ({len(cookies)} cookies)")
    print(f"2. is_logged_in(): {is_logged}")
    print(f"3. verify_login(): {verify_result}")

    if verify_result:
        print(f"\n[SUCCESS] Real cookies are VALID!")
        print("  - Cookies parsed correctly")
        print("  - All required cookies present")
        print("  - Server recognizes the session")
        print("  - Login status is ACTIVE")

        # 保存为正式的cookies.json
        print(f"\n[Step 7] Saving to cookies.json...")
        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        print("  [OK] Saved valid cookies to cookies.json")

        return True
    else:
        print(f"\n[FAILED] Real cookies are INVALID or EXPIRED")
        print("  Possible reasons:")
        print("    1. Cookies copied incorrectly")
        print("    2. Session expired (time-based)")
        print("    3. IP address changed")
        print("    4. Server invalidated the session")

        return False


def test_http_request_details():
    """详细测试HTTP请求"""
    print("\n" + "="*70)
    print("Detailed HTTP Request Test")
    print("="*70)

    # 解析cookies
    cookie_string = """uuid_tt_dd=10_37073029060-1744764649384-303632; fid=20_15857838147-1744764651083-624090; Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac=1756454268,1756794401,1756872706,1758008490; _clck=z6powj%5E2%5Efzg%5E0%5E1932; c_ab_test=1; csdn_newcert_weixin_42273662=1; csdn_newcert_ForagerNet=1; c_adb=1; UN=weixin_42273662; p_uid=U110000; c_segment=0; dc_sid=8e6fec4bf4250baabf2365000343ad95; creative_btn_mp=3; loginbox_strategy=%7B%22blog-threeH-dialog-exp11tipShowTimes%22%3A2%2C%22blog-threeH-dialog-exp11%22%3A%22%22%2C%22taskId%22%3A317%2C%22abCheckTime%22%3A1760090145808%2C%22version%22%3A%22ExpA%22%2C%22nickName%22%3A%22InternetHerder%22%2C%22blog-threeH-dialog-expa%22%3A1759194998941%7D; c_first_page=https%3A//passport.csdn.net/login%3Fcode%3Dapplets; c_first_ref=default; dc_session_id=10_1760094486089.436866; c_dsid=11_1760094486868.083569; hide_login=1; c-sidebar-collapse=0; c_utm_medium=distribute.pc_feed_vip_blog_category.none-task-blog-classify_tag-1-151814724-null-null.nonecase; SESSION=e4118eaa-02b0-4e5d-8187-bfc0f3759bde; UserName=weixin_42273662; UserInfo=ac830d3a4e4e4bdc912ec5c8b372b1d8; UserToken=ac830d3a4e4e4bdc912ec5c8b372b1d8; UserNick=InternetHerder; AU=2DC; BT=1760094685893; c_pref=https%3A//blog.csdn.net/%3Fspm%3D1001.2101.3001.4477; c_ref=https%3A//blog.csdn.net/weixin_42273662%3Ftype%3Dblog; log_Id_click=13; c_page_id=default; log_Id_pv=9; log_Id_view=367; dc_tos=t3wy3s"""

    cookies = parse_cookie_string(cookie_string)

    # 创建requests session
    import requests
    session = requests.Session()

    # 设置cookies
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.csdn.net')

    # 设置User-Agent
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    })

    print("\n[Test 1] Request to https://www.csdn.net/")
    try:
        response = session.get("https://www.csdn.net/", timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  URL: {response.url}")
        print(f"  Length: {len(response.text)} bytes")

        # 检查内容
        checks = {
            '登录': '登录' in response.text,
            '退出': '退出' in response.text,
            '个人中心': '个人中心' in response.text,
            'InternetHerder': 'InternetHerder' in response.text,
            'weixin_42273662': 'weixin_42273662' in response.text,
        }

        print("\n  Content checks:")
        for key, found in checks.items():
            status = "[FOUND]" if found else "[NOT FOUND]"
            print(f"    {status} '{key}'")

        # 判断
        if checks['退出'] or checks['个人中心'] or checks['InternetHerder']:
            print("\n  [SUCCESS] Logged in (found user-specific content)")
            return True
        elif checks['登录'] and not checks['退出']:
            print("\n  [FAILED] Not logged in (found login, no logout)")
            return False
        else:
            print("\n  [UNCERTAIN] Cannot determine")
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def main():
    print("\n" + "*"*70)
    print("  Test verify_login() with Real Cookies from Browser")
    print("*"*70)

    # 测试1: 使用AuthService
    result1 = test_with_real_cookies()

    # 测试2: 详细HTTP测试
    result2 = test_http_request_details()

    print("\n" + "="*70)
    print("Final Summary")
    print("="*70)
    print(f"  AuthService verify_login(): {'PASS' if result1 else 'FAIL'}")
    print(f"  Direct HTTP test: {'PASS' if result2 else 'FAIL'}")

    if result1 and result2:
        print("\n  [SUCCESS] All tests passed!")
        print("  Real cookies are working correctly!")
        return 0
    else:
        print("\n  [FAILED] Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
