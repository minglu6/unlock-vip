"""
测试 API 认证系统
"""
import requests
import json

# API 配置
BASE_URL = "http://localhost:8000"

def test_without_api_key():
    """测试未提供 API Key"""
    print("\n1️⃣ 测试未提供 API Key...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/article/download",
            json={"url": "https://blog.csdn.net/test/article/details/123"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def test_with_invalid_api_key():
    """测试无效的 API Key"""
    print("\n2️⃣ 测试无效的 API Key...")
    try:
        headers = {"X-API-Key": "invalid_key_12345"}
        response = requests.post(
            f"{BASE_URL}/api/article/download",
            headers=headers,
            json={"url": "https://blog.csdn.net/test/article/details/123"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def test_with_valid_api_key(api_key):
    """测试有效的 API Key"""
    print("\n3️⃣ 测试有效的 API Key...")
    try:
        headers = {"X-API-Key": api_key}
        response = requests.post(
            f"{BASE_URL}/api/article/download",
            headers=headers,
            json={"url": "https://blog.csdn.net/weixin_41896770/article/details/139574308"},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        if result.get('content'):
            # 截断 HTML 内容显示
            result['content'] = result['content'][:200] + "... (已截断)"
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def create_test_api_key():
    """通过管理接口创建测试 API Key"""
    print("\n0️⃣ 创建测试 API Key...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/api-keys",
            json={
                "name": "测试密钥",
                "user_id": "test_user",
                "rate_limit_per_minute": 10,
                "rate_limit_per_hour": 100,
                "rate_limit_per_day": 1000,
                "description": "用于测试的API密钥"
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Key 创建成功!")
            print(f"密钥: {data['key']}")
            return data['key']
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


def list_api_keys():
    """列出所有 API Keys"""
    print("\n4️⃣ 列出所有 API Keys...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/api-keys")
        if response.status_code == 200:
            keys = response.json()
            print(f"找到 {len(keys)} 个密钥:")
            for key in keys:
                print(f"\n  ID: {key['id']}")
                print(f"  名称: {key['name']}")
                print(f"  密钥: {key['key']}")
                print(f"  状态: {'✅ 启用' if key['is_active'] else '❌ 禁用'}")
                print(f"  总请求数: {key['total_requests']}")
        else:
            print(f"❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def view_logs(api_key=None):
    """查看请求日志"""
    print("\n5️⃣ 查看请求日志...")
    try:
        params = {"limit": 10}
        if api_key:
            params["api_key"] = api_key
        
        response = requests.get(f"{BASE_URL}/api/admin/logs", params=params)
        if response.status_code == 200:
            logs = response.json()
            print(f"找到 {len(logs)} 条日志:")
            for log in logs:
                status = "✅" if log['success'] else "❌"
                print(f"\n  {status} [{log['created_at']}]")
                print(f"  端点: {log['endpoint']}")
                print(f"  API Key: {log['api_key'][:16]}...")
                print(f"  状态码: {log['status_code']}")
                if log['processing_time']:
                    print(f"  处理时间: {log['processing_time']}ms")
                if log['error_message']:
                    print(f"  错误: {log['error_message']}")
        else:
            print(f"❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def main():
    """主测试流程"""
    print("="*60)
    print("🔐 API 认证系统测试")
    print("="*60)
    
    # 测试未认证请求
    test_without_api_key()
    
    # 测试无效密钥
    test_with_invalid_api_key()
    
    # 创建测试密钥
    api_key = create_test_api_key()
    
    if api_key:
        # 测试有效密钥
        test_with_valid_api_key(api_key)
        
        # 列出所有密钥
        list_api_keys()
        
        # 查看日志
        view_logs()
    else:
        print("\n⚠️  无法创建测试密钥，跳过后续测试")
        print("提示：请确保数据库已正确配置并初始化")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
