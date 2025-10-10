"""
直接测试清理任务（不需要 FastAPI 服务）
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.tasks.cleanup_tasks import get_downloads_stats, cleanup_old_downloads

def test_cleanup_direct():
    print("=" * 60)
    print("🧹 直接测试文件清理功能（无需 API 服务）")
    print("=" * 60)
    
    # 测试 1: 获取统计信息
    print("\n【测试 1】获取下载目录统计")
    try:
        stats = get_downloads_stats()
        print("✅ 成功获取统计信息:")
        print(f"   - 总文件数: {stats['total_files']}")
        print(f"   - 总大小: {stats.get('total_size_formatted', 'N/A')}")
        
        if stats['total_files'] > 0:
            print(f"   - 文件年龄分布:")
            print(f"     * 1天内: {stats['files_by_age']['within_1_day']}")
            print(f"     * 7天内: {stats['files_by_age']['within_7_days']}")
            print(f"     * 30天内: {stats['files_by_age']['within_30_days']}")
            print(f"     * 30天以上: {stats['files_by_age']['over_30_days']}")
            
            if stats.get('oldest_file'):
                print(f"   - 最老文件:")
                print(f"     名称: {stats['oldest_file']['name'][:60]}...")
                print(f"     年龄: {stats['oldest_file']['age_days']} 天")
                print(f"     大小: {stats['oldest_file']['size_formatted']}")
            
            if stats.get('newest_file'):
                print(f"   - 最新文件:")
                print(f"     名称: {stats['newest_file']['name'][:60]}...")
                print(f"     年龄: {stats['newest_file']['age_days']} 天")
            
            if stats.get('largest_file'):
                print(f"   - 最大文件:")
                print(f"     名称: {stats['largest_file']['name'][:60]}...")
                print(f"     大小: {stats['largest_file']['size_formatted']}")
        else:
            print("   ℹ️  下载目录为空")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 2: 演练模式清理（7天）
    print("\n【测试 2】演练模式清理（7天前的文件）")
    try:
        result = cleanup_old_downloads(days=7, dry_run=True)
        
        if result['success']:
            print(f"✅ 演练完成:")
            print(f"   - 扫描文件: {result['scanned_files']}")
            print(f"   - 将删除: {result['deleted_files']} 个")
            print(f"   - 将释放空间: {result['deleted_size']} 字节")
            print(f"   - 将保留: {result['kept_files']} 个")
            
            if result['deleted_list']:
                print(f"   - 将删除的文件（前5个）:")
                for file in result['deleted_list'][:5]:
                    print(f"     * {file['name'][:50]}...")
                    print(f"       年龄: {file['age_days']} 天, 大小: {file['size_formatted']}")
            
            if result['errors']:
                print(f"   ⚠️  错误:")
                for error in result['errors']:
                    print(f"     - {error}")
        else:
            print(f"❌ 清理失败: {result.get('errors', [])}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 3: 演练模式清理（30天）
    print("\n【测试 3】演练模式清理（30天前的文件）")
    try:
        result = cleanup_old_downloads(days=30, dry_run=True)
        
        if result['success']:
            print(f"✅ 演练完成:")
            print(f"   - 将删除: {result['deleted_files']} 个文件")
            print(f"   - 将保留: {result['kept_files']} 个文件")
        else:
            print(f"❌ 清理失败")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    # 测试 4: 演练模式清理（1天）
    print("\n【测试 4】演练模式清理（1天前的文件）")
    try:
        result = cleanup_old_downloads(days=1, dry_run=True)
        
        if result['success']:
            print(f"✅ 演练完成:")
            print(f"   - 将删除: {result['deleted_files']} 个文件")
            print(f"   - 将保留: {result['kept_files']} 个文件")
            
            if result['deleted_files'] > 0:
                print("\n   ⚠️  警告: 有文件超过1天，请确认是否需要删除")
        else:
            print(f"❌ 清理失败")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("   - 所有测试都在演练模式下运行，未实际删除文件")
    print("   - 如需实际删除，修改 dry_run=False")
    print("   - 建议通过 API 接口操作，有更好的访问控制")
    print("=" * 60)

if __name__ == "__main__":
    test_cleanup_direct()
