"""
测试最新的cookies
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth_service import AuthService


def test_latest_cookies():
    """测试最新的cookies"""
    print("="*70)
    print("Test with Latest Cookies")
    print("="*70)

    # 最新的cookies（JSON格式）
    cookies = {
        "https_waf_cookie": "5ffeb15c-ef08-4af3b843f6d07cc1c5e40e4b2e740e834b4f",
        "uuid_tt_dd": "10_18809227780-1760094772168-704803",
        "dc_session_id": "10_1760094772168.833375",
        "bc_bot_session": "1760094774f4623bb172dc142a",
        "bc_bot_token": "11760094774f4623bb172dc142ae7863c",
        "bc_bot_rules": "R11",
        "bc_bot_fp": "c572fd6c668113e4f427a56dde47558f",
        "c_pref": "default",
        "fid": "20_98802502461-1760094773318-101117",
        "c_first_ref": "default",
        "c_first_page": "https%3A//passport.csdn.net/login%3Fcode%3Dapplets",
        "c_dsid": "11_1760094773319.109247",
        "c_segment": "3",
        "HMACCOUNT_BFESS": "B17B56EFF3F6B0C5",
        "Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac": "1760094774",
        "HMACCOUNT": "B17B56EFF3F6B0C5",
        "hide_login": "1",
        "dc_sid": "3850e00bbf6e64eabe928c73b72c081d",
        "SESSION": "NDBkMDQ2ODctZDEzMi00NTgxLWFhYmItNTcxMWQxODI5NmZm",
        "waf_captcha_marker": "5ea9bce139d6f135cf1dc02ace68aef13102d828fb36fb6d6668c7783cb7a1be",
        "yd_captcha_token": "MTc2MDA5NDc5OTMyNV8xMTIuMjguMTU0LjE1NF82NDJmYjc0NjcxYWE4MjBjOThiMzY1MGVkOTg2NzAyOWI5Ng%3D%3D",
        "UserName": "weixin_42273662",
        "UserInfo": "90fe1a17d4524fab80fe20df913c3ed7",
        "UserToken": "90fe1a17d4524fab80fe20df913c3ed7",
        "UserNick": "InternetHerder",
        "AU": "2DC",
        "UN": "weixin_42273662",
        "BT": "1760094799648",
        "p_uid": "U110000",
        "csrfToken": "ldjuhYLySdqhxs4DN5DpjsSj",
        "c-sidebar-collapse": "0",
        "c_ab_test": "1",
        "creative_popup": "%7B%22arrowIcon%22%3A%22https%3A//i-operation.csdnimg.cn/images/0f13ec529b6b4195ad99894f76653e56.png%22%2C%22img%22%3A%22https%3A//i-operation.csdnimg.cn/images/d32fa98221a943049dffd1ea13841d61.png%22%2C%22imgStyle%22%3A%22height%3A%2088px%3B%22%2C%22darkCfg%22%3A%7B%7D%2C%22role%22%3A%22noPost%22%2C%22report%22%3A%7B%22spm%22%3A%223001.11120%22%2C%22extra%22%3A%22%22%7D%2C%22style%22%3A%22%22%2C%22arrowIconStyle%22%3A%22%22%2C%22url%22%3A%22https%3A//mp.csdn.net/edit%22%2C%22newTab%22%3Afalse%2C%22userName%22%3A%22weixin_42273662%22%7D",
        "csdn_newcert_weixin_42273662": "1",
        "c_ref": "https%3A//www.csdn.net/",
        "_bl_uid": "31mkCghzk2yrz30vU5RUpUC75URd",
        "log_Id_click": "4",
        "c_page_id": "default",
        "log_Id_pv": "4",
        "creative_btn_mp": "3",
        "Hm_lpvt_6bcd52f51e9b3dce32bec4a3997715ac": "1760094831",
        "CLID": "070cbf75c29f4a8f982393dbf2ace460.20251010.20261010",
        "_clck": "7vpfsz%5E2%5Eg01%5E0%5E2109",
        "dc_tos": "t3wxv3",
        "BAIDUID_BFESS": "1BF31DC9A78485F07541F0F44F49D2CE:FG=1",
        "log_Id_view": "115",
        "_clsk": "5o7fb9%5E1760094832324%5E1%5E0%5Ed.clarity.ms%2Fcollect",
        "MUID": "017F9508BF4D69BC3EC58389BE946805",
        "MR": "0",
        "SRM_B": "017F9508BF4D69BC3EC58389BE946805",
        "SM": "C",
        "ANONCHK": "0"
    }

    print(f"\n[Step 1] Cookies loaded")
    print(f"  Total: {len(cookies)} cookies")

    # 检查关键cookies
    print("\n[Step 2] Checking key cookies...")
    key_cookies = ['UserToken', 'UserInfo', 'UserName', 'SESSION']
    for key in key_cookies:
        if key in cookies:
            value = cookies[key]
            preview = value[:30] + "..." if len(value) > 30 else value
            print(f"  [OK] {key}: {preview}")
        else:
            print(f"  [MISS] {key}: NOT FOUND")

    # 保存到文件
    print("\n[Step 3] Saving to cookies.json...")
    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)
    print("  [OK] Saved to cookies.json")

    # 测试 AuthService
    print("\n[Step 4] Testing with AuthService...")
    auth_service = AuthService(use_captcha_service=False, debug=False)
    auth_service.cookies = cookies

    # 测试 is_logged_in
    print("\n[Step 5] Testing is_logged_in()...")
    is_logged = auth_service.is_logged_in()
    print(f"  Result: {is_logged}")

    if not is_logged:
        print("  [FAIL] Missing required cookies")
        required = ['UserToken', 'UserInfo', 'UserName']
        for req in required:
            if req not in cookies:
                print(f"    Missing: {req}")
        return False

    # 测试 verify_login
    print("\n[Step 6] Testing verify_login()...")
    print("  Making HTTP request to verify login status...")
    verify_result = auth_service.verify_login()

    print(f"\n{'='*70}")
    print("Test Results")
    print(f"{'='*70}")
    print(f"  Cookies count: {len(cookies)}")
    print(f"  is_logged_in(): {is_logged}")
    print(f"  verify_login(): {verify_result}")

    if verify_result:
        print(f"\n[SUCCESS] Latest cookies are VALID!")
        print("  - All required cookies present")
        print("  - Server recognizes the session")
        print("  - Login status is ACTIVE")
        return True
    else:
        print(f"\n[FAILED] Latest cookies are INVALID")
        print("  Session may have expired")
        return False


def test_article_service():
    """测试 ArticleService 的 ensure_login"""
    print("\n" + "="*70)
    print("Test ArticleService.ensure_login()")
    print("="*70)

    from app.services.article_service import ArticleService

    # 首先保存cookies
    cookies = {
        "UserToken": "90fe1a17d4524fab80fe20df913c3ed7",
        "UserInfo": "90fe1a17d4524fab80fe20df913c3ed7",
        "UserName": "weixin_42273662",
        "SESSION": "NDBkMDQ2ODctZDEzMi00NTgxLWFhYmItNTcxMWQxODI5NmZm",
    }

    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)

    print("\n[Test] Creating ArticleService...")
    article_service = ArticleService()

    print("\n[Test] Calling ensure_login()...")
    try:
        article_service.ensure_login()
        print("\n[SUCCESS] ensure_login() completed without errors")
        return True
    except Exception as e:
        print(f"\n[FAILED] ensure_login() raised exception: {e}")
        return False


def main():
    print("\n" + "*"*70)
    print("  Test Latest Cookies")
    print("*"*70)

    # 测试1: AuthService
    result1 = test_latest_cookies()

    # 测试2: ArticleService
    result2 = test_article_service()

    print("\n" + "="*70)
    print("Final Summary")
    print("="*70)
    print(f"  AuthService test: {'PASS' if result1 else 'FAIL'}")
    print(f"  ArticleService test: {'PASS' if result2 else 'FAIL'}")

    if result1 and result2:
        print("\n[SUCCESS] All tests passed!")
        print("Latest cookies are working correctly!")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
