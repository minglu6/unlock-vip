#!/usr/bin/env python3
"""
生成管理员主密钥

用于保护管理接口，防止未授权访问
"""
import secrets

def generate_admin_key():
    """生成一个安全的管理员密钥"""
    key = secrets.token_urlsafe(32)
    
    print("=" * 60)
    print("🔐 管理员主密钥已生成")
    print("=" * 60)
    print()
    print(f"密钥: {key}")
    print()
    print("请将此密钥添加到 .env 文件中：")
    print()
    print(f"ADMIN_MASTER_KEY={key}")
    print()
    print("⚠️  安全提示：")
    print("1. 请妥善保管此密钥，不要泄露给他人")
    print("2. 不要将此密钥提交到 Git 仓库")
    print("3. 定期更换密钥以提高安全性")
    print("4. 生产环境建议使用更长的密钥")
    print("=" * 60)

if __name__ == "__main__":
    generate_admin_key()
