#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSDN资源文件下载服务
处理CSDN下载资源的请求和链接获取
"""
import requests
import json
import logging
import urllib3
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


# 全局线程池管理器
class FileDownloadThreadPool:
    """文件下载服务线程池管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._executor = ThreadPoolExecutor(
                max_workers=4,
                thread_name_prefix="FileDownload"
            )
            self._initialized = True
            logger.info("文件下载服务线程池初始化完成: 4个工作线程")
    
    @property
    def executor(self):
        """获取线程池执行器"""
        return self._executor
    
    def shutdown(self, wait=True):
        """关闭线程池"""
        logger.info("正在关闭文件下载服务线程池...")
        self._executor.shutdown(wait=wait)
        logger.info("文件下载服务线程池已关闭")


# 获取全局线程池实例
def get_thread_pool() -> ThreadPoolExecutor:
    """获取文件下载服务的线程池"""
    return FileDownloadThreadPool().executor


class FileDownloadService:
    """CSDN资源文件下载服务"""
    
    # CSDN下载API端点
    DOWNLOAD_API = "https://download.csdn.net/api/source/detail/v1/download"
    
    def __init__(self, cookies: Optional[Dict[str, str]] = None):
        """
        初始化下载服务
        
        Args:
            cookies: CSDN登录cookies字典
        """
        self.cookies = cookies or {}
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建配置好的requests会话"""
        session = requests.Session()
        
        # 设置请求头，模拟浏览器
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/json',
            'Origin': 'https://download.csdn.net',
            'Referer': 'https://download.csdn.net/',
            'DNT': '1',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
        })
        
        # 设置cookies
        if self.cookies:
            session.cookies.update(self.cookies)
        
        return session
    
    def extract_source_id_from_url(self, url: str) -> Optional[str]:
        """
        从CSDN下载页面URL中提取sourceId
        
        Args:
            url: CSDN下载页面URL，如 https://download.csdn.net/download/weixin_43385320/91316313
            
        Returns:
            sourceId字符串，如果提取失败返回None
        """
        try:
            # 解析URL
            parsed = urlparse(url)
            
            # 检查是否是CSDN下载域名
            if 'download.csdn.net' not in parsed.netloc:
                logger.warning(f"URL不是CSDN下载域名: {url}")
                return None
            
            # 从路径中提取sourceId
            # URL格式: /download/用户名/sourceId 或 /download/用户名/sourceId?参数
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 3 and path_parts[0] == 'download':
                source_id = path_parts[2]
                logger.info(f"从URL提取sourceId: {source_id}")
                return source_id
            else:
                logger.warning(f"无法从URL路径中提取sourceId: {url}")
                return None
                
        except Exception as e:
            logger.error(f"提取sourceId时出错: {str(e)}", exc_info=True)
            return None
    
    def get_download_link(self, source_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        获取资源的实际下载链接
        
        Args:
            source_id: CSDN资源ID
            
        Returns:
            (成功标志, 下载链接, 错误消息)
        """
        try:
            logger.info(f"正在请求下载链接，sourceId: {source_id}")
            
            # 构建请求数据
            payload = {
                "sourceId": int(source_id)
            }
            
            # 发送POST请求（禁用SSL验证）
            response = self.session.post(
                self.DOWNLOAD_API,
                json=payload,
                timeout=30,
                allow_redirects=True,
                verify=False  # 禁用SSL证书验证
            )
            
            logger.info(f"API响应状态码: {response.status_code}")
            
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = f"API请求失败，状态码: {response.status_code}"
                logger.error(error_msg)
                return False, None, error_msg
            
            # 解析JSON响应
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                error_msg = f"解析响应JSON失败: {str(e)}"
                logger.error(error_msg)
                return False, None, error_msg
            
            # 检查响应code
            code = response_data.get('code')
            message = response_data.get('message', 'Unknown error')
            
            if code != 200:
                error_msg = f"API返回错误，code: {code}, message: {message}"
                logger.error(error_msg)
                return False, None, error_msg
            
            # 提取下载链接
            download_url = response_data.get('data')
            
            if not download_url:
                error_msg = "响应中未找到下载链接"
                logger.error(error_msg)
                return False, None, error_msg
            
            logger.info(f"成功获取下载链接: {download_url[:100]}...")
            return True, download_url, None
            
        except requests.RequestException as e:
            error_msg = f"网络请求异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"获取下载链接时发生未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg
    
    def get_download_link_from_url(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        从CSDN下载页面URL直接获取下载链接
        
        Args:
            url: CSDN下载页面URL
            
        Returns:
            (成功标志, 下载链接, 错误消息)
        """
        # 提取sourceId
        source_id = self.extract_source_id_from_url(url)
        
        if not source_id:
            error_msg = "无法从URL中提取sourceId"
            logger.error(error_msg)
            return False, None, error_msg
        
        # 获取下载链接
        return self.get_download_link(source_id)
    
    def update_cookies(self, cookies: Dict[str, str]) -> None:
        """
        更新cookies
        
        Args:
            cookies: 新的cookies字典
        """
        self.cookies = cookies
        self.session.cookies.update(cookies)
        logger.info("Cookies已更新")
    
    def load_cookies_from_file(self, cookies_file: str = "cookies.json") -> bool:
        """
        从JSON文件加载cookies
        
        Args:
            cookies_file: cookies文件路径
            
        Returns:
            是否成功加载
        """
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies_dict = json.load(f)
            
            self.update_cookies(cookies_dict)
            logger.info(f"成功从 {cookies_file} 加载cookies，共{len(cookies_dict)}个")
            return True
            
        except FileNotFoundError:
            logger.warning(f"Cookies文件不存在: {cookies_file}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"解析cookies文件失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"加载cookies时发生错误: {str(e)}", exc_info=True)
            return False


# 便捷函数
def get_csdn_download_link(url: str, cookies: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    便捷函数：获取CSDN资源下载链接
    
    Args:
        url: CSDN下载页面URL
        cookies: 可选的cookies字典
        
    Returns:
        (成功标志, 下载链接, 错误消息)
        
    Example:
        >>> success, link, error = get_csdn_download_link("https://download.csdn.net/download/user/12345")
        >>> if success:
        >>>     print(f"下载链接: {link}")
        >>> else:
        >>>     print(f"错误: {error}")
    """
    service = FileDownloadService(cookies)
    return service.get_download_link_from_url(url)


def get_download_link_by_id(source_id: str, cookies: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    便捷函数：通过sourceId获取下载链接
    
    Args:
        source_id: CSDN资源ID
        cookies: 可选的cookies字典
        
    Returns:
        (成功标志, 下载链接, 错误消息)
        
    Example:
        >>> success, link, error = get_download_link_by_id("91316313")
        >>> if success:
        >>>     print(f"下载链接: {link}")
    """
    service = FileDownloadService(cookies)
    return service.get_download_link(source_id)


if __name__ == '__main__':
    """测试代码"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试URL
    test_url = "https://download.csdn.net/download/weixin_43385320/91316313"
    
    print("=" * 80)
    print("CSDN资源下载服务测试")
    print("=" * 80)
    
    # 创建服务实例
    service = FileDownloadService()
    
    # 尝试从文件加载cookies
    service.load_cookies_from_file("cookies.json")
    
    # 测试提取sourceId
    print(f"\n测试URL: {test_url}")
    source_id = service.extract_source_id_from_url(test_url)
    print(f"提取的sourceId: {source_id}")
    
    # 测试获取下载链接
    if source_id:
        print(f"\n正在获取下载链接...")
        success, download_link, error = service.get_download_link(source_id)
        
        if success:
            print(f"✅ 成功获取下载链接:")
            print(f"   链接: {download_link[:150]}...")
            print(f"   完整链接长度: {len(download_link)} 字符")
        else:
            print(f"❌ 获取失败:")
            print(f"   错误: {error}")
    
    # 测试便捷函数
    print(f"\n测试便捷函数...")
    success, link, error = get_csdn_download_link(test_url)
    
    if success:
        print(f"✅ 成功: {link[:100]}...")
    else:
        print(f"❌ 失败: {error}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
