"""
测试管理员认证功能

验证：
1. 没有管理员密钥时访问管理接口 - 应该返回 422
2. 使用错误的管理员密钥 - 应该返回 403
3. 使用正确的管理员密钥 - 应该成功
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
ADMIN_KEY = os.getenv("ADMIN_MASTER_KEY")

def test_admin_auth():
    print("=" * 60)
    print("🔐 测试管理员认证功能")
    print("=" * 60)
    
    # 测试 1: 没有管理员密钥
    print("\n【测试 1】没有提供管理员密钥")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/api-keys")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 422:
            print("✅ 测试通过：正确返回 422（缺少必需参数）")
        else:
            print("❌ 测试失败：应该返回 422")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试 2: 错误的管理员密钥
    print("\n【测试 2】使用错误的管理员密钥")
    try:
        headers = {"X-Admin-Key": "wrong_admin_key_here"}
        response = requests.get(f"{BASE_URL}/api/admin/api-keys", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code == 403:
            print("✅ 测试通过：正确返回 403（无效的管理员密钥）")
        else:
            print("❌ 测试失败：应该返回 403")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试 3: 正确的管理员密钥
    print("\n【测试 3】使用正确的管理员密钥")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.get(f"{BASE_URL}/api/admin/api-keys", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 测试通过：成功获取 API Keys 列表")
            print(f"   - 共有 {len(data)} 个 API Key")
            if data:
                print(f"   - 第一个密钥: {data[0]['name']} (ID: {data[0]['id']})")
        else:
            print(f"❌ 测试失败：应该返回 200，实际返回 {response.status_code}")
            print(f"响应: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试 4: 创建 API Key（需要管理员密钥）
    print("\n【测试 4】使用管理员密钥创建新的 API Key")
    try:
        headers = {
            "X-Admin-Key": ADMIN_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "name": "管理员测试密钥",
            "rate_limit_per_minute": 60,
            "rate_limit_per_hour": 1000,
            "rate_limit_per_day": 10000,
            "description": "用于测试管理员认证功能"
        }
        response = requests.post(f"{BASE_URL}/api/admin/api-keys", headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 测试通过：成功创建 API Key")
            print(f"   - ID: {result['id']}")
            print(f"   - 名称: {result['name']}")
            print(f"   - 密钥: {result['key']}")
            print(f"   - 描述: {result.get('description', 'N/A')}")
        else:
            print(f"❌ 测试失败：应该返回 200，实际返回 {response.status_code}")
            print(f"响应: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试 5: 查看统计（需要管理员密钥）
    print("\n【测试 5】使用管理员密钥查看统计信息")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.get(f"{BASE_URL}/api/admin/api-keys/1/stats?days=7", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code in [200, 404]:  # 404 表示密钥不存在，也是正常的
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 测试通过：成功获取统计信息")
                print(f"   - 总请求数: {result['total_requests']}")
                print(f"   - 成功请求: {result['successful_requests']}")
                print(f"   - 失败请求: {result['failed_requests']}")
                if result['avg_processing_time']:
                    print(f"   - 平均处理时间: {result['avg_processing_time']:.2f} ms")
            else:
                print(f"✅ 测试通过：API Key ID=1 不存在（正常）")
        else:
            print(f"❌ 测试失败：应该返回 200 或 404，实际返回 {response.status_code}")
            print(f"响应: {response.json()}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    if not ADMIN_KEY:
        print("❌ 错误：未在 .env 文件中找到 ADMIN_MASTER_KEY")
        print("请先运行: python generate_admin_key.py")
        exit(1)
    
    print(f"使用管理员密钥: {ADMIN_KEY[:10]}...{ADMIN_KEY[-10:]}")
    print()
    
    test_admin_auth()
