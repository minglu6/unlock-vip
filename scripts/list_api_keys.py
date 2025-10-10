#!/usr/bin/env python3
"""
查看数据库中的 API Keys
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.db.database import SessionLocal
from app.db.models import APIKey
from datetime import datetime

def list_api_keys():
    """列出所有API密钥"""
    db = SessionLocal()
    
    try:
        api_keys = db.query(APIKey).all()
        
        print("=" * 80)
        print("🔑 数据库中的 API Keys")
        print("=" * 80)
        
        if not api_keys:
            print("\n❌ 数据库中没有任何 API Key")
            print("\n💡 提示: 运行以下命令生成一个测试 API Key:")
            print("   python generate_test_key.py")
            print()
            return None
        
        print(f"\n找到 {len(api_keys)} 个 API Key:\n")
        
        for idx, key in enumerate(api_keys, 1):
            print(f"【{idx}】")
            print(f"  ID: {key.id}")
            print(f"  密钥: {key.key}")
            print(f"  名称: {key.name or '未命名'}")
            print(f"  描述: {key.description or '无'}")
            print(f"  状态: {'✅ 激活' if key.is_active else '❌ 禁用'}")
            print(f"  频率限制: {key.rate_limit_per_hour or 1000} 次/小时")
            print(f"  总请求数: {key.total_requests or 0}")
            print(f"  创建时间: {key.created_at}")
            print(f"  最后使用: {key.last_used_at or '从未使用'}")
            print()
        
        # 返回第一个激活的 API Key
        active_keys = [k for k in api_keys if k.is_active]
        if active_keys:
            print("=" * 80)
            print(f"✅ 推荐使用的 API Key: {active_keys[0].key}")
            print("=" * 80)
            print()
            return active_keys[0].key
        else:
            print("=" * 80)
            print("⚠️  警告: 所有 API Key 都已禁用")
            print("=" * 80)
            return None
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    list_api_keys()
