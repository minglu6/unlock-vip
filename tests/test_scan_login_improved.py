"""
测试改进后的微信扫码登录功能
"""
import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.auth_service import AuthService

def test_scan_output_dir():
    """测试扫码输出目录获取功能"""
    print("=" * 60)
    print("测试扫码输出目录获取功能")
    print("=" * 60)

    auth_service = AuthService()

    # 测试获取输出目录
    save_dir = auth_service._get_scan_output_dir()

    if save_dir:
        print(f"[OK] 成功获取可写的输出目录: {save_dir}")

        # 验证目录是否真的可写
        test_file = os.path.join(save_dir, "test_write.txt")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print(f"[OK] 目录写入测试通过")
        except Exception as e:
            print(f"[ERROR] 目录写入测试失败: {e}")
    else:
        print("[ERROR] 未能获取可写的输出目录")

    print("\n" + "=" * 60)

def test_scan_login_with_headful():
    """测试微信扫码登录（有界面模式，方便观察）"""
    print("=" * 60)
    print("测试微信扫码登录（有界面模式）")
    print("=" * 60)
    print("\n注意：此测试会打开浏览器窗口，请观察二维码检测过程")
    print("测试将在5秒后开始...")

    import time
    time.sleep(5)

    auth_service = AuthService(headless=False)

    try:
        # 首先访问CSDN登录页
        auth_service._init_browser()
        auth_service.page.goto("https://passport.csdn.net/login")
        auth_service.page.wait_for_timeout(2000)

        print("\n开始测试微信扫码登录检测...")

        # 尝试扫码登录（等待10秒观察）
        result = auth_service._attempt_scan_login(wait_ms=10000)

        if result:
            print("\n[OK] 扫码登录成功！")
        else:
            print("\n[Info] 扫码登录未完成（可能是超时或未扫码）")
            print("这是正常的，因为我们只是在测试二维码检测功能")

    except Exception as e:
        print(f"\n[ERROR] 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        auth_service.close()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

def main():
    """主函数"""
    import sys

    # 如果有命令行参数，使用参数；否则默认测试输出目录
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        print("\n运行完整扫码登录测试（需要人工观察）")
        test_scan_login_with_headful()
    else:
        print("\n运行快速测试（仅测试输出目录获取）")
        print("提示：如需完整测试，请运行: python test_scan_login_improved.py full")
        test_scan_output_dir()

if __name__ == "__main__":
    main()
