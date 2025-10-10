#!/usr/bin/env python3
"""
完整的API集成测试
测试流程：提交任务 → 查询状态 → 获取结果
"""
import requests
import time
import json
import sys
from datetime import datetime

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_complete_flow():
    """测试完整的API流程"""
    base_url = "http://localhost:8000"
    
    # 使用数据库中的有效API密钥
    api_key = "RW56J2xRxRcqlWY9pxveW0vCp-558dwiwZh7TXrK54k"
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # 使用真实的未解锁CSDN文章
    test_url = "https://blog.csdn.net/rasssel/article/details/151838126"
    
    print_section("🚀 API完整流程测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {base_url}")
    print(f"测试URL: {test_url}")

    # 步骤0: 健康检查
    print_section("步骤0: 服务健康检查")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务运行正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 服务状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {str(e)}")
        print("   请确保服务已启动:")
        print("   1. python run.py")
        print("   2. celery -A celery_worker worker --loglevel=info --pool=solo")
        return False

    # 步骤1: 提交任务
    print_section("步骤1: 提交文章下载任务")
    submit_data = {
        "url": test_url
    }

    try:
        print(f"正在提交任务...")
        response = requests.post(
            f"{base_url}/api/article/submit",
            headers=headers,
            json=submit_data,
            timeout=10
        )

        print(f"响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 任务提交失败")
            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            if response.status_code == 401:
                print("   提示: API密钥无效，请先生成有效的API密钥")
                print("   运行: python generate_admin_key.py")
            return False

        submit_result = response.json()
        task_id = submit_result.get("task_id")
        print(f"✅ 任务提交成功!")
        print(f"   任务ID: {task_id}")
        print(f"   状态: {submit_result.get('status')}")
        print(f"   消息: {submit_result.get('message')}")

    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 无法连接到服务器")
        print("   请确保FastAPI服务已启动: python run.py")
        return False
    except Exception as e:
        print(f"❌ 任务提交异常: {type(e).__name__}: {str(e)}")
        return False

    # 步骤2: 轮询任务状态
    print_section("步骤2: 轮询任务状态")
    print(f"任务ID: {task_id}")
    print("开始轮询...\n")
    
    max_retries = 120  # 最多轮询120次，约2分钟
    retry_count = 0
    last_status = None

    while retry_count < max_retries:
        try:
            response = requests.get(
                f"{base_url}/api/article/task/{task_id}/status",
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                print(f"\n❌ 查询状态失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False

            status_result = response.json()
            status = status_result.get("status")
            progress = status_result.get("progress")

            # 只在状态改变时打印详细信息
            if status != last_status:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] 状态: {status}", end="")
                if progress is not None:
                    print(f" (进度: {progress}%)")
                else:
                    print()
                last_status = status
            else:
                # 相同状态只打印点
                print(".", end="", flush=True)

            if status == "SUCCESS":
                print(f"\n✅ 任务处理完成! (共轮询 {retry_count+1} 次，耗时 {retry_count+1} 秒)")
                break
            elif status == "FAILURE":
                error = status_result.get("error", "未知错误")
                print(f"\n❌ 任务处理失败: {error}")
                if "traceback" in status_result:
                    print(f"   错误详情: {status_result['traceback']}")
                return False
            elif status == "ERROR":
                error = status_result.get("error", "系统错误")
                print(f"\n❌ 系统错误: {error}")
                return False

        except Exception as e:
            print(f"\n❌ 查询状态异常: {type(e).__name__}: {str(e)}")
            return False

        retry_count += 1
        time.sleep(1)  # 等待1秒后再次查询

    if retry_count >= max_retries:
        print(f"\n❌ 轮询超时 (已尝试 {max_retries} 次)")
        print("   可能原因:")
        print("   1. Celery worker未启动")
        print("   2. 网络连接问题")
        print("   3. 文章下载耗时过长")
        return False

    # 步骤3: 获取任务结果
    print_section("步骤3: 获取任务结果")
    print(f"任务ID: {task_id}")
    
    try:
        print("正在获取结果...")
        response = requests.get(
            f"{base_url}/api/article/task/{task_id}/result",
            headers=headers,
            timeout=10
        )

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 425:
            print("⚠️  任务还未准备好结果，请稍后重试")
            return False
        elif response.status_code != 200:
            print(f"❌ 获取结果失败")
            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False

        result_data = response.json()

        if result_data.get("success"):
            content = result_data.get("content")
            file_size = result_data.get("file_size")
            title = result_data.get("title")

            print(f"✅ 成功获取文章内容!")
            print(f"   标题: {title or '未知'}")
            print(f"   文件大小: {file_size:,} 字节" if file_size else "   文件大小: 未知")
            print(f"   内容长度: {len(content):,} 字符" if content else "   内容: 空")

            # 保存内容到文件进行验证
            if content:
                output_file = f"test_output_{task_id[:8]}.html"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   已保存到: {output_file}")
                
                # 显示内容预览
                preview_length = 500
                if len(content) > preview_length:
                    print(f"\n内容预览 (前{preview_length}字符):")
                    print("-" * 70)
                    print(content[:preview_length] + "...")
                    print("-" * 70)
            
            print("\n✅ 测试完成!")
            return True
        else:
            error_msg = result_data.get("error", "未知错误")
            print(f"❌ 结果标记为失败: {error_msg}")
            return False

    except Exception as e:
        print(f"❌ 获取结果异常: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*70)
    print("  CSDN文章解析API - 完整流程测试")
    print("="*70)
    
    success = test_complete_flow()
    
    print_section("测试总结")
    if success:
        print("✅ 所有测试通过!")
        print("\n测试覆盖:")
        print("  ✓ 服务健康检查")
        print("  ✓ 任务提交")
        print("  ✓ 任务状态查询")
        print("  ✓ 任务结果获取")
        print("  ✓ 文章内容解析")
        sys.exit(0)
    else:
        print("❌ 测试失败!")
        print("\n故障排查步骤:")
        print("  1. 检查FastAPI服务是否运行: http://localhost:8000/health")
        print("  2. 检查Celery worker是否运行")
        print("  3. 检查Redis是否运行")
        print("  4. 检查MySQL是否运行")
        print("  5. 检查API密钥是否有效")
        sys.exit(1)

if __name__ == "__main__":
    main()
