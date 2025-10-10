#!/usr/bin/env python3
"""
生成测试用的API密钥
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.db.database import SessionLocal
from app.db.models import APIKey
import secrets
from datetime import datetime

def generate_test_api_key():
    """生成一个测试用的API密钥"""
    db = SessionLocal()
    
    try:
        # 生成密钥
        key = "sk_test_" + secrets.token_urlsafe(24)
        
        # 创建API密钥记录
        api_key = APIKey(
            key=key,
            name="测试密钥",
            description="用于API测试的密钥",
            is_active=True,
            rate_limit=100,  # 每小时100次请求
            created_at=datetime.utcnow()
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        print("=" * 70)
        print("🔑 测试API密钥已生成")
        print("=" * 70)
        print()
        print(f"密钥ID: {api_key.id}")
        print(f"密钥: {api_key.key}")
        print(f"名称: {api_key.name}")
        print(f"频率限制: {api_key.rate_limit} 次/小时")
        print(f"状态: {'激活' if api_key.is_active else '禁用'}")
        print()
        print("请将此密钥用于测试:")
        print(f"api_key = \"{api_key.key}\"")
        print()
        print("=" * 70)
        
        return api_key.key
        
    except Exception as e:
        db.rollback()
        print(f"❌ 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_api_key()
