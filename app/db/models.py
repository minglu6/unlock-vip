"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index, BigInteger
from sqlalchemy.sql import func
from app.db.database import Base

class APIKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False, comment="API密钥")
    name = Column(String(100), nullable=False, comment="密钥名称/用途")
    user_id = Column(String(50), index=True, comment="用户ID")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    
    # 频率限制配置
    rate_limit_per_minute = Column(Integer, default=60, comment="每分钟请求限制")
    rate_limit_per_hour = Column(Integer, default=1000, comment="每小时请求限制")
    rate_limit_per_day = Column(Integer, default=10000, comment="每天请求限制")
    
    # 统计信息
    total_requests = Column(BigInteger, default=0, comment="总请求次数")
    last_used_at = Column(DateTime(timezone=True), comment="最后使用时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    
    # 备注
    description = Column(Text, comment="备注说明")

    def __repr__(self):
        return f"<APIKey(key={self.key[:8]}..., name={self.name}, active={self.is_active})>"


class APIRequestLog(Base):
    """API请求日志表"""
    __tablename__ = "api_request_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    api_key = Column(String(64), index=True, nullable=False, comment="使用的API密钥")
    user_id = Column(String(50), index=True, comment="用户ID")
    
    # 请求信息
    endpoint = Column(String(200), nullable=False, comment="请求端点")
    method = Column(String(10), nullable=False, comment="请求方法")
    url = Column(Text, comment="请求的文章URL")
    
    # 响应信息
    status_code = Column(Integer, comment="响应状态码")
    success = Column(Boolean, default=False, comment="是否成功")
    error_message = Column(Text, comment="错误信息")
    
    # 性能指标
    processing_time = Column(Integer, comment="处理时间（毫秒）")
    response_size = Column(BigInteger, comment="响应大小（字节）")
    
    # 客户端信息
    ip_address = Column(String(45), index=True, comment="客户端IP")
    user_agent = Column(Text, comment="User Agent")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # 复合索引用于统计查询
    __table_args__ = (
        Index('idx_api_key_created', 'api_key', 'created_at'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<APIRequestLog(api_key={self.api_key[:8]}..., endpoint={self.endpoint}, success={self.success})>"
