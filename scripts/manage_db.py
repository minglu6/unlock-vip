"""
数据库管理工具
用于创建初始API密钥和查看统计信息
"""
import sys
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.db.models import APIKey, APIRequestLog

def create_api_key(
    name: str,
    user_id: str = None,
    rate_limit_per_minute: int = 60,
    rate_limit_per_hour: int = 1000,
    rate_limit_per_day: int = 10000,
    expires_days: int = None
):
    """创建一个新的API密钥"""
    db = SessionLocal()
    try:
        # 生成随机密钥
        api_key = secrets.token_urlsafe(32)
        
        # 计算过期时间
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        # 创建数据库记录
        db_api_key = APIKey(
            key=api_key,
            name=name,
            user_id=user_id,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
            expires_at=expires_at
        )
        
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        
        print(f"\n✅ API密钥创建成功！")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"密钥ID: {db_api_key.id}")
        print(f"API Key: {db_api_key.key}")
        print(f"名称: {db_api_key.name}")
        print(f"用户ID: {db_api_key.user_id or '无'}")
        print(f"每分钟限制: {db_api_key.rate_limit_per_minute}")
        print(f"每小时限制: {db_api_key.rate_limit_per_hour}")
        print(f"每天限制: {db_api_key.rate_limit_per_day}")
        print(f"过期时间: {db_api_key.expires_at or '永不过期'}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        return db_api_key
        
    finally:
        db.close()


def list_api_keys():
    """列出所有API密钥"""
    db = SessionLocal()
    try:
        api_keys = db.query(APIKey).all()
        
        if not api_keys:
            print("\n⚠️  没有找到任何API密钥")
            return
        
        print(f"\n📋 共找到 {len(api_keys)} 个API密钥:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        for key in api_keys:
            status = "✅ 启用" if key.is_active else "❌ 禁用"
            expired = ""
            if key.expires_at:
                if key.expires_at < datetime.now():
                    expired = " (已过期)"
                else:
                    expired = f" (剩余{(key.expires_at - datetime.now()).days}天)"
            
            print(f"\nID: {key.id} | {status}{expired}")
            print(f"名称: {key.name}")
            print(f"密钥: {key.key}")
            print(f"用户ID: {key.user_id or '无'}")
            print(f"总请求数: {key.total_requests}")
            print(f"最后使用: {key.last_used_at or '从未使用'}")
            print(f"限制: {key.rate_limit_per_minute}/分钟, {key.rate_limit_per_hour}/小时, {key.rate_limit_per_day}/天")
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
    finally:
        db.close()


def show_stats():
    """显示统计信息"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        
        # 总体统计
        total_keys = db.query(func.count(APIKey.id)).scalar()
        active_keys = db.query(func.count(APIKey.id)).filter(APIKey.is_active == True).scalar()
        total_requests = db.query(func.count(APIRequestLog.id)).scalar()
        successful_requests = db.query(func.count(APIRequestLog.id)).filter(APIRequestLog.success == True).scalar()
        
        print(f"\n📊 系统统计:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"API密钥总数: {total_keys}")
        print(f"启用的密钥: {active_keys}")
        print(f"总请求次数: {total_requests}")
        print(f"成功请求: {successful_requests}")
        if total_requests > 0:
            success_rate = (successful_requests / total_requests) * 100
            print(f"成功率: {success_rate:.2f}%")
        
        # 最近7天的请求趋势
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_requests = db.query(func.count(APIRequestLog.id)).filter(
            APIRequestLog.created_at >= seven_days_ago
        ).scalar()
        
        print(f"\n最近7天请求: {recent_requests}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
    finally:
        db.close()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
使用方法:
    python manage_db.py init                    # 初始化数据库
    python manage_db.py create <名称>           # 创建新的API密钥
    python manage_db.py list                    # 列出所有API密钥
    python manage_db.py stats                   # 显示统计信息
    
示例:
    python manage_db.py create "测试密钥"
    python manage_db.py create "生产环境" --user-id user123 --expires 365
        """)
        return
    
    command = sys.argv[1]
    
    if command == "init":
        print("正在初始化数据库...")
        init_db()
        print("✅ 数据库初始化完成！")
        
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ 错误: 请提供密钥名称")
            print("示例: python manage_db.py create '测试密钥'")
            return
        
        name = sys.argv[2]
        user_id = None
        expires_days = None
        
        # 解析可选参数
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--user-id" and i + 1 < len(sys.argv):
                user_id = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--expires" and i + 1 < len(sys.argv):
                expires_days = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        create_api_key(name, user_id=user_id, expires_days=expires_days)
        
    elif command == "list":
        list_api_keys()
        
    elif command == "stats":
        show_stats()
        
    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
