"""
测试临时目录修复
"""
import tempfile
import os
import sys

def test_temp_dir():
    """测试临时目录创建"""
    print("="*60)
    print("Testing temp directory creation")
    print("="*60)

    # 测试原来的方式（会失败）
    print("\n1. Test old way (with /tmp):")
    try:
        temp_dir = tempfile.mkdtemp(prefix="pw_user_data_", dir="/tmp")
        print(f"   [FAIL] Should have failed but created: {temp_dir}")
        os.rmdir(temp_dir)
    except FileNotFoundError as e:
        print(f"   [EXPECTED] Failed as expected: {e}")
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {e}")

    # 测试新的方式（应该成功）
    print("\n2. Test new way (system default):")
    try:
        temp_dir = tempfile.mkdtemp(prefix="pw_user_data_")
        print(f"   [PASS] Created successfully: {temp_dir}")

        # 验证目录存在
        if os.path.exists(temp_dir):
            print(f"   [PASS] Directory exists")
        else:
            print(f"   [FAIL] Directory does not exist")

        # 清理
        os.rmdir(temp_dir)
        print(f"   [PASS] Cleaned up successfully")

        return True

    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return False

def main():
    print("\nPlatform info:")
    print(f"  OS: {sys.platform}")
    print(f"  Python: {sys.version}")
    print(f"  Temp dir: {tempfile.gettempdir()}")
    print()

    result = test_temp_dir()

    print("\n" + "="*60)
    if result:
        print("[SUCCESS] Temp directory fix is working!")
    else:
        print("[FAILED] Temp directory fix failed!")
    print("="*60)

    return 0 if result else 1

if __name__ == "__main__":
    exit(main())
