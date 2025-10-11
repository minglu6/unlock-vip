"""
简化的登录测试 - 避免Windows控制台编码问题
"""
import os
import sys

# 设置环境变量强制使用UTF-8编码（必须在导入其他模块前设置）
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth_service import AuthService
from app.core.config import settings

# 删除现有cookies
if os.path.exists("cookies.json"):
    os.remove("cookies.json")
    print("Removed existing cookies.json")

print("\n" + "="*60)
print("Testing CSDN Login")
print("="*60)
print(f"Account: {settings.CSDN_USERNAME}")
print(f"Captcha service: {settings.CAPTCHA_SERVICE}")
print()

# 创建认证服务（关闭debug模式避免emoji输出）
auth_service = AuthService(use_captcha_service=True, debug=False)

print("Starting login...")
try:
    success = auth_service.login(
        username=settings.CSDN_USERNAME,
        password=settings.CSDN_PASSWORD
    )

    if success:
        print("\n[SUCCESS] Login successful!")

        # 检查cookies
        if os.path.exists("cookies.json"):
            import json
            with open("cookies.json", "r") as f:
                cookies = json.load(f)
            print(f"Cookies saved: {len(cookies)} items")

            # 检查关键cookies
            required = ['UserToken', 'UserInfo', 'UserName']
            for key in required:
                exists = "YES" if key in cookies else "NO"
                print(f"  {key}: {exists}")
        else:
            print("[WARN] cookies.json not created")
    else:
        print("\n[FAILED] Login failed")

except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    auth_service.close()
