"""
测试登录功能的内存占用
"""
import os
import sys
import psutil
import time

sys.path.insert(0, os.path.dirname(__file__))

from app.services.auth_service import AuthService
from app.core.config import settings


def get_memory_info():
    """获取当前进程的内存信息"""
    process = psutil.Process()
    mem_info = process.memory_info()

    return {
        'rss_mb': mem_info.rss / 1024 / 1024,  # 物理内存 (MB)
        'vms_mb': mem_info.vms / 1024 / 1024,  # 虚拟内存 (MB)
    }


def format_memory(mb):
    """格式化内存显示"""
    if mb < 1024:
        return f"{mb:.2f} MB"
    else:
        return f"{mb/1024:.2f} GB"


def main():
    print("="*70)
    print("Playwright Login Memory Usage Test")
    print("="*70)

    # 系统总内存
    total_memory = psutil.virtual_memory().total / 1024 / 1024 / 1024
    available_memory = psutil.virtual_memory().available / 1024 / 1024 / 1024
    print(f"\nSystem Memory:")
    print(f"  Total: {total_memory:.2f} GB")
    print(f"  Available: {available_memory:.2f} GB")

    # 初始内存
    print(f"\n{'='*70}")
    print("Step 1: Initial Memory (Before Import)")
    print(f"{'='*70}")
    mem_initial = get_memory_info()
    print(f"  Physical Memory (RSS): {format_memory(mem_initial['rss_mb'])}")
    print(f"  Virtual Memory (VMS): {format_memory(mem_initial['vms_mb'])}")

    # 创建AuthService实例
    print(f"\n{'='*70}")
    print("Step 2: After Creating AuthService Instance")
    print(f"{'='*70}")

    auth_service = AuthService(use_captcha_service=False, debug=False)
    time.sleep(1)

    mem_after_init = get_memory_info()
    print(f"  Physical Memory (RSS): {format_memory(mem_after_init['rss_mb'])}")
    print(f"  Virtual Memory (VMS): {format_memory(mem_after_init['vms_mb'])}")
    print(f"  Increase: {format_memory(mem_after_init['rss_mb'] - mem_initial['rss_mb'])}")

    # 启动Playwright浏览器
    print(f"\n{'='*70}")
    print("Step 3: After Starting Playwright Browser")
    print(f"{'='*70}")
    print("  (This will launch Chromium browser)")

    try:
        # 调用内部方法启动浏览器
        auth_service._init_browser()
        time.sleep(3)  # 等待浏览器完全启动

        mem_after_browser = get_memory_info()
        print(f"  Physical Memory (RSS): {format_memory(mem_after_browser['rss_mb'])}")
        print(f"  Virtual Memory (VMS): {format_memory(mem_after_browser['vms_mb'])}")
        print(f"  Increase from Init: {format_memory(mem_after_browser['rss_mb'] - mem_after_init['rss_mb'])}")
        print(f"  Total Increase: {format_memory(mem_after_browser['rss_mb'] - mem_initial['rss_mb'])}")

        # 访问页面后的内存
        print(f"\n{'='*70}")
        print("Step 4: After Loading CSDN Login Page")
        print(f"{'='*70}")

        if auth_service.page:
            auth_service.page.goto('https://passport.csdn.net/login?code=applets', wait_until="domcontentloaded")
            time.sleep(3)

        mem_after_page = get_memory_info()
        print(f"  Physical Memory (RSS): {format_memory(mem_after_page['rss_mb'])}")
        print(f"  Virtual Memory (VMS): {format_memory(mem_after_page['vms_mb'])}")
        print(f"  Increase from Browser: {format_memory(mem_after_page['rss_mb'] - mem_after_browser['rss_mb'])}")
        print(f"  Total Increase: {format_memory(mem_after_page['rss_mb'] - mem_initial['rss_mb'])}")

        # 峰值内存
        print(f"\n{'='*70}")
        print("Peak Memory Usage")
        print(f"{'='*70}")
        print(f"  Peak Physical Memory: {format_memory(mem_after_page['rss_mb'])}")
        print(f"  Peak Virtual Memory: {format_memory(mem_after_page['vms_mb'])}")

        # 估算Chromium进程的内存
        print(f"\n{'='*70}")
        print("Chromium Browser Processes")
        print(f"{'='*70}")

        current_process = psutil.Process()
        children = current_process.children(recursive=True)

        total_chromium_memory = 0
        print(f"  Found {len(children)} child processes:")

        for i, child in enumerate(children, 1):
            try:
                child_mem = child.memory_info().rss / 1024 / 1024
                total_chromium_memory += child_mem
                print(f"    Process {i}: {format_memory(child_mem)}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        print(f"  Total Chromium Memory: {format_memory(total_chromium_memory)}")

        # 总结
        print(f"\n{'='*70}")
        print("Summary")
        print(f"{'='*70}")
        print(f"  Python Process: {format_memory(mem_after_page['rss_mb'])}")
        print(f"  Chromium Processes: {format_memory(total_chromium_memory)}")
        print(f"  Total Memory Used: {format_memory(mem_after_page['rss_mb'] + total_chromium_memory)}")

        print(f"\n{'='*70}")
        print("Recommended System Requirements")
        print(f"{'='*70}")
        total_used = mem_after_page['rss_mb'] + total_chromium_memory
        recommended = total_used * 1.5  # 留50%余量

        print(f"  Minimum RAM: {format_memory(total_used)}")
        print(f"  Recommended RAM: {format_memory(recommended)}")
        print(f"  Recommended RAM (rounded up): {int(recommended/1024) + 1} GB")

        print(f"\n{'='*70}")
        print("Memory Breakdown")
        print(f"{'='*70}")
        python_percent = (mem_after_page['rss_mb'] / (mem_after_page['rss_mb'] + total_chromium_memory)) * 100
        chromium_percent = (total_chromium_memory / (mem_after_page['rss_mb'] + total_chromium_memory)) * 100

        print(f"  Python: {python_percent:.1f}% ({format_memory(mem_after_page['rss_mb'])})")
        print(f"  Chromium: {chromium_percent:.1f}% ({format_memory(total_chromium_memory)})")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        print(f"\n{'='*70}")
        print("Cleaning up...")
        print(f"{'='*70}")
        auth_service.close()
        time.sleep(2)

        mem_final = get_memory_info()
        print(f"  Final Memory: {format_memory(mem_final['rss_mb'])}")
        print(f"  Memory Released: {format_memory(mem_after_page['rss_mb'] - mem_final['rss_mb'])}")

    print(f"\n{'='*70}")
    print("Test Complete")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
