"""
测试文件清理功能

验证：
1. 获取下载目录统计
2. 演练模式清理（不实际删除）
3. 实际清理（可选）
"""
import requests
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

BASE_URL = "http://localhost:8000"
ADMIN_KEY = os.getenv("ADMIN_MASTER_KEY")

def test_cleanup_features():
    print("=" * 60)
    print("🧹 测试文件清理功能")
    print("=" * 60)
    
    headers = {"X-Admin-Key": ADMIN_KEY}
    
    # 测试 1: 获取下载目录统计
    print("\n【测试 1】获取下载目录统计")
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/cleanup/stats",
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ 成功获取统计信息:")
            print(f"   - 总文件数: {stats['total_files']}")
            print(f"   - 总大小: {stats.get('total_size_formatted', 'N/A')}")
            print(f"   - 文件年龄分布:")
            print(f"     * 1天内: {stats['files_by_age']['within_1_day']}")
            print(f"     * 7天内: {stats['files_by_age']['within_7_days']}")
            print(f"     * 30天内: {stats['files_by_age']['within_30_days']}")
            print(f"     * 30天以上: {stats['files_by_age']['over_30_days']}")
            
            if stats.get('oldest_file'):
                print(f"   - 最老文件: {stats['oldest_file']['name']}")
                print(f"     年龄: {stats['oldest_file']['age_days']} 天")
                print(f"     大小: {stats['oldest_file']['size_formatted']}")
            
            if stats.get('newest_file'):
                print(f"   - 最新文件: {stats['newest_file']['name']}")
                print(f"     年龄: {stats['newest_file']['age_days']} 天")
            
            if stats.get('largest_file'):
                print(f"   - 最大文件: {stats['largest_file']['name']}")
                print(f"     大小: {stats['largest_file']['size_formatted']}")
        else:
            print(f"❌ 请求失败: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试 2: 获取清理配置
    print("\n【测试 2】获取清理配置")
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/cleanup/config",
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            config = response.json()
            print("✅ 当前配置:")
            print(f"   - 启用状态: {'启用' if config['enabled'] else '禁用'}")
            print(f"   - 保留天数: {config['retention_days']} 天")
            print(f"   - 执行计划: {config['schedule']}")
            print(f"   - 时区: {config['timezone']}")
        else:
            print(f"❌ 请求失败: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试 3: 演练模式清理（7天）
    print("\n【测试 3】演练模式清理（7天前的文件）")
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/cleanup/run",
            headers=headers,
            params={"days": 7, "dry_run": True}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 演练完成:")
            print(f"   - 扫描文件: {result['scanned_files']}")
            print(f"   - 将删除: {result['deleted_files']} 个")
            print(f"   - 将释放空间: {result['deleted_size']} 字节")
            print(f"   - 将保留: {result['kept_files']} 个")
            
            if result['deleted_list']:
                print(f"   - 将删除的文件:")
                for file in result['deleted_list'][:5]:  # 只显示前5个
                    print(f"     * {file['name'][:50]}...")
                    print(f"       年龄: {file['age_days']} 天, 大小: {file['size_formatted']}")
        else:
            print(f"❌ 请求失败: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试 4: 演练模式清理（30天）
    print("\n【测试 4】演练模式清理（30天前的文件）")
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/cleanup/run",
            headers=headers,
            params={"days": 30, "dry_run": True}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 演练完成:")
            print(f"   - 将删除: {result['deleted_files']} 个文件")
            print(f"   - 将保留: {result['kept_files']} 个文件")
        else:
            print(f"❌ 请求失败: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 提示：实际清理
    print("\n" + "=" * 60)
    print("💡 提示：")
    print("   如需实际删除文件，请运行:")
    print(f"   curl -X POST '{BASE_URL}/api/admin/cleanup/run?days=7&dry_run=false' \\")
    print(f"     -H 'X-Admin-Key: {ADMIN_KEY[:10]}...'")
    print("=" * 60)

if __name__ == "__main__":
    if not ADMIN_KEY:
        print("❌ 错误：未在 .env 文件中找到 ADMIN_MASTER_KEY")
        exit(1)
    
    test_cleanup_features()
