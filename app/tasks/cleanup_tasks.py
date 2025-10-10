"""
文件清理任务 - 定期删除旧的下载文件

功能：
1. 定期清理超过指定天数的 HTML 文件
2. 记录清理日志
3. 支持手动触发清理
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import logging

from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_downloads_dir() -> Path:
    """获取下载目录路径"""
    project_root = Path(__file__).parent.parent.parent
    downloads_dir = project_root / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    return downloads_dir


def get_file_age_days(file_path: Path) -> float:
    """获取文件的年龄（天数）"""
    try:
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        age = datetime.now() - file_mtime
        return age.total_seconds() / 86400  # 转换为天数
    except Exception as e:
        logger.error(f"获取文件 {file_path} 年龄失败: {e}")
        return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


@celery_app.task(name='tasks.cleanup_old_downloads')
def cleanup_old_downloads(days: int = 7, dry_run: bool = False) -> Dict:
    """
    清理超过指定天数的下载文件
    
    Args:
        days: 保留天数，默认 7 天
        dry_run: 是否为演练模式（不实际删除），默认 False
    
    Returns:
        清理结果统计
    """
    downloads_dir = get_downloads_dir()
    
    result = {
        "success": True,
        "dry_run": dry_run,
        "retention_days": days,
        "scanned_files": 0,
        "deleted_files": 0,
        "deleted_size": 0,
        "kept_files": 0,
        "kept_size": 0,
        "errors": [],
        "deleted_list": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        logger.info(f"开始清理任务: 保留 {days} 天内的文件, 演练模式: {dry_run}")
        
        # 遍历下载目录中的所有 HTML 文件
        for file_path in downloads_dir.glob("*.html"):
            result["scanned_files"] += 1
            
            try:
                file_age = get_file_age_days(file_path)
                file_size = file_path.stat().st_size
                
                if file_age > days:
                    # 文件超过保留期限
                    if not dry_run:
                        file_path.unlink()
                        logger.info(f"已删除: {file_path.name} (年龄: {file_age:.1f}天, 大小: {format_file_size(file_size)})")
                    else:
                        logger.info(f"[演练] 将删除: {file_path.name} (年龄: {file_age:.1f}天, 大小: {format_file_size(file_size)})")
                    
                    result["deleted_files"] += 1
                    result["deleted_size"] += file_size
                    result["deleted_list"].append({
                        "name": file_path.name,
                        "age_days": round(file_age, 2),
                        "size": file_size,
                        "size_formatted": format_file_size(file_size)
                    })
                else:
                    # 文件在保留期限内
                    result["kept_files"] += 1
                    result["kept_size"] += file_size
                    logger.debug(f"保留: {file_path.name} (年龄: {file_age:.1f}天)")
                    
            except Exception as e:
                error_msg = f"处理文件 {file_path.name} 时出错: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
        
        # 汇总日志
        logger.info(f"清理完成: 扫描 {result['scanned_files']} 个文件, "
                   f"{'将删除' if dry_run else '已删除'} {result['deleted_files']} 个 "
                   f"({format_file_size(result['deleted_size'])}), "
                   f"保留 {result['kept_files']} 个 "
                   f"({format_file_size(result['kept_size'])})")
        
    except Exception as e:
        result["success"] = False
        error_msg = f"清理任务失败: {str(e)}"
        logger.error(error_msg)
        result["errors"].append(error_msg)
    
    return result


@celery_app.task(name='tasks.get_downloads_stats')
def get_downloads_stats() -> Dict:
    """
    获取下载目录的统计信息
    
    Returns:
        目录统计信息
    """
    downloads_dir = get_downloads_dir()
    
    stats = {
        "total_files": 0,
        "total_size": 0,
        "files_by_age": {
            "within_1_day": 0,
            "within_7_days": 0,
            "within_30_days": 0,
            "over_30_days": 0
        },
        "oldest_file": None,
        "newest_file": None,
        "largest_file": None,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        html_files = list(downloads_dir.glob("*.html"))
        stats["total_files"] = len(html_files)
        
        if not html_files:
            return stats
        
        # 统计信息
        oldest_age = 0
        newest_age = float('inf')
        largest_size = 0
        
        for file_path in html_files:
            try:
                file_size = file_path.stat().st_size
                file_age = get_file_age_days(file_path)
                
                stats["total_size"] += file_size
                
                # 按年龄分类
                if file_age <= 1:
                    stats["files_by_age"]["within_1_day"] += 1
                elif file_age <= 7:
                    stats["files_by_age"]["within_7_days"] += 1
                elif file_age <= 30:
                    stats["files_by_age"]["within_30_days"] += 1
                else:
                    stats["files_by_age"]["over_30_days"] += 1
                
                # 找最老的文件
                if file_age > oldest_age:
                    oldest_age = file_age
                    stats["oldest_file"] = {
                        "name": file_path.name,
                        "age_days": round(file_age, 2),
                        "size": file_size,
                        "size_formatted": format_file_size(file_size)
                    }
                
                # 找最新的文件
                if file_age < newest_age:
                    newest_age = file_age
                    stats["newest_file"] = {
                        "name": file_path.name,
                        "age_days": round(file_age, 2),
                        "size": file_size,
                        "size_formatted": format_file_size(file_size)
                    }
                
                # 找最大的文件
                if file_size > largest_size:
                    largest_size = file_size
                    stats["largest_file"] = {
                        "name": file_path.name,
                        "age_days": round(file_age, 2),
                        "size": file_size,
                        "size_formatted": format_file_size(file_size)
                    }
                    
            except Exception as e:
                logger.error(f"处理文件 {file_path.name} 统计时出错: {e}")
        
        stats["total_size_formatted"] = format_file_size(stats["total_size"])
        
    except Exception as e:
        logger.error(f"获取下载统计失败: {e}")
    
    return stats
