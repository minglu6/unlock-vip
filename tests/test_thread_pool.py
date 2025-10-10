#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试文件下载服务线程池功能
验证并发请求处理能力
"""
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# API配置
API_BASE_URL = "http://127.0.0.1:8000"
API_KEY = "test-key-123"

# 测试URL列表
TEST_URLS = [
    "https://download.csdn.net/download/weixin_41645323/91316313",
    "https://download.csdn.net/download/weixin_41645323/91316313",
    "https://download.csdn.net/download/weixin_41645323/91316313",
    "https://download.csdn.net/download/weixin_41645323/91316313",
    "https://download.csdn.net/download/weixin_41645323/91316313",
    "https://download.csdn.net/download/weixin_41645323/91316313",
    "https://download.csdn.net/download/weixin_41645323/91316313",
    "https://download.csdn.net/download/weixin_41645323/91316313",
]


def send_download_request(url: str, request_id: int) -> dict:
    """发送单个下载请求"""
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/file/get-download-link",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json={"url": url},
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        result = {
            "request_id": request_id,
            "status_code": response.status_code,
            "elapsed_time": elapsed,
            "success": False,
            "error": None
        }
        
        if response.status_code == 200:
            data = response.json()
            result["success"] = data.get("success", False)
            result["source_id"] = data.get("source_id")
            result["has_download_url"] = bool(data.get("download_url"))
            result["message"] = data.get("message")
            result["error"] = data.get("error")
        else:
            result["error"] = f"HTTP {response.status_code}"
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "request_id": request_id,
            "status_code": 0,
            "elapsed_time": elapsed,
            "success": False,
            "error": str(e)
        }


def test_concurrent_requests(num_requests: int = 8):
    """测试并发请求"""
    print(f"\n{'='*60}")
    print(f"🧪 测试文件下载服务线程池 - 并发请求测试")
    print(f"{'='*60}")
    print(f"📊 测试参数:")
    print(f"   - 并发请求数: {num_requests}")
    print(f"   - 服务端线程池: 4个工作线程")
    print(f"   - 客户端线程池: {num_requests}个线程")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    # 使用客户端线程池模拟并发请求
    results = []
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        # 提交所有请求
        future_to_id = {
            executor.submit(send_download_request, TEST_URLS[i % len(TEST_URLS)], i+1): i+1
            for i in range(num_requests)
        }
        
        print("📤 已提交所有请求，等待响应...\n")
        
        # 收集结果
        for future in as_completed(future_to_id):
            request_id = future_to_id[future]
            try:
                result = future.result()
                results.append(result)
                
                status = "✅" if result["success"] else "❌"
                print(f"{status} 请求 #{result['request_id']:02d} | "
                      f"耗时: {result['elapsed_time']:.2f}s | "
                      f"状态: {result['status_code']} | "
                      f"消息: {result.get('message', result.get('error', 'N/A'))}")
                
            except Exception as e:
                print(f"❌ 请求 #{request_id:02d} | 异常: {str(e)}")
    
    total_time = time.time() - start_time
    
    # 统计结果
    print(f"\n{'='*60}")
    print(f"📈 测试结果统计")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    avg_time = sum(r["elapsed_time"] for r in results) / len(results) if results else 0
    max_time = max((r["elapsed_time"] for r in results), default=0)
    min_time = min((r["elapsed_time"] for r in results), default=0)
    
    print(f"总请求数: {len(results)}")
    print(f"成功数: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"失败数: {failed_count} ({failed_count/len(results)*100:.1f}%)")
    print(f"\n⏱️  时间统计:")
    print(f"   - 总耗时: {total_time:.2f}s")
    print(f"   - 平均响应时间: {avg_time:.2f}s")
    print(f"   - 最快响应: {min_time:.2f}s")
    print(f"   - 最慢响应: {max_time:.2f}s")
    print(f"   - 吞吐量: {len(results)/total_time:.2f} 请求/秒")
    
    # 错误分析
    if failed_count > 0:
        print(f"\n❌ 失败详情:")
        for r in results:
            if not r["success"]:
                print(f"   - 请求 #{r['request_id']}: {r.get('error', 'Unknown error')}")
    
    print(f"{'='*60}\n")
    
    # 判断测试结果
    if success_count >= len(results) * 0.8:  # 80%成功率
        print("✅ 测试通过！线程池工作正常")
        return True
    else:
        print("❌ 测试失败！成功率低于80%")
        return False


def test_health_check():
    """测试健康检查端点"""
    print(f"\n{'='*60}")
    print(f"🏥 健康检查测试")
    print(f"{'='*60}\n")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/file/health",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务状态: {data.get('status', 'unknown')}")
            print(f"📦 服务名称: {data.get('service', 'unknown')}")
            print(f"🍪 Cookies可用: {data.get('cookies_available', False)}")
            print(f"🔗 API端点: {data.get('api_endpoint', 'unknown')}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查异常: {str(e)}")
        return False
    finally:
        print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 文件下载服务线程池测试套件")
    print("="*60)
    
    # 测试1: 健康检查
    health_ok = test_health_check()
    
    if not health_ok:
        print("⚠️  服务未就绪，跳过并发测试")
        exit(1)
    
    # 测试2: 并发请求 (8个请求，服务端4个线程)
    test_concurrent_requests(num_requests=8)
    
    # 测试3: 高并发请求 (16个请求，测试队列)
    print("\n" + "="*60)
    print("🔥 高并发测试 (16个并发请求)")
    print("="*60)
    test_concurrent_requests(num_requests=16)
    
    print("\n✨ 所有测试完成！\n")
