"""
测试验证码检测逻辑
"""
import os
import sys

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
import time

print("="*60)
print("Testing Captcha Detection")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print("\n1. Navigating to CSDN login page...")
    page.goto('https://passport.csdn.net/login?code=applets')
    time.sleep(3)

    print("\n2. Looking for password login...")
    try:
        other_login = page.locator("text=其他登录方式")
        if other_login.count() > 0:
            other_login.first.click()
            time.sleep(1.5)
            print("   [OK] Clicked 'other login'")

            passwd_login = page.locator("span.login-third-passwd")
            if passwd_login.count() > 0:
                page.evaluate("(el) => el.click()", passwd_login.first.element_handle())
                print("   [OK] Clicked password login")
                time.sleep(2)
    except Exception as e:
        print(f"   [WARN] {e}")

    print("\n3. Filling username and password...")
    try:
        username_input = page.wait_for_selector("input.base-input-text[autocomplete='username']", timeout=5000)
        password_input = page.wait_for_selector("input.base-input-text[autocomplete='current-password']", timeout=5000)

        # Use test credentials or prompt
        test_username = "test_user"
        test_password = "test_pass"

        username_input.fill(test_username)
        password_input.fill(test_password)
        print(f"   [OK] Filled username: {test_username}")
        print(f"   [OK] Filled password: ***")

        time.sleep(1)
    except Exception as e:
        print(f"   [ERROR] {e}")

    print("\n4. Clicking login button...")
    try:
        login_button = page.wait_for_selector("button.base-button", timeout=5000)
        login_button.click()
        print("   [OK] Clicked login button")
        time.sleep(3)
    except Exception as e:
        print(f"   [ERROR] {e}")

    print("\n5. Detecting captcha...")
    captcha_selectors = [
        ("Title text '请完成安全验证'", "xpath=//*[contains(text(), '请完成安全验证')]"),
        ("Title text '安全验证'", "xpath=//*[contains(text(), '安全验证')]"),
        ("Caption title class", ".caption__title"),
        ("Canvas element", "canvas"),
        ("Verify panel", ".verify-img-panel"),
        ("Verify canvas", ".verify-img-panel canvas"),
    ]

    captcha_found = False
    for name, selector in captcha_selectors:
        locator = page.locator(selector)
        count = locator.count()
        print(f"\n   Checking: {name}")
        print(f"   Selector: {selector}")
        print(f"   Count: {count}")

        if count > 0:
            try:
                elem = locator.first
                visible = elem.is_visible()
                print(f"   Visible: {visible}")

                if visible:
                    print(f"   [FOUND] Captcha detected with: {name}")
                    captcha_found = True

                    # Try to take screenshot
                    try:
                        elem.screenshot(path=f"captcha_element_{name.replace(' ', '_')}.png")
                        print(f"   [OK] Screenshot saved")
                    except Exception as e:
                        print(f"   [WARN] Cannot screenshot: {e}")
            except Exception as e:
                print(f"   [ERROR] {e}")

    if captcha_found:
        print("\n" + "="*60)
        print("[SUCCESS] Captcha detected!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("[FAILED] No captcha detected")
        print("="*60)

    print("\nPress Enter to close browser...")
    input()

    browser.close()
