"""
Cookie 解析工具
支持两种格式：
1. 浏览器复制的 cookie 字符串格式: "name1=value1; name2=value2; ..."
2. JSON 格式: {"name1": "value1", "name2": "value2"}
"""
import json
import logging
from typing import Dict, Union
from urllib.parse import unquote

logger = logging.getLogger(__name__)


def parse_cookie_string(cookie_string: str) -> Dict[str, str]:
    """
    解析浏览器复制的 cookie 字符串

    Args:
        cookie_string: cookie 字符串，格式如 "name1=value1; name2=value2"

    Returns:
        Dict[str, str]: cookie 字典
    """
    cookies = {}

    # 分割 cookie 项
    cookie_pairs = cookie_string.split(';')

    for pair in cookie_pairs:
        pair = pair.strip()
        if not pair or '=' not in pair:
            continue

        # 分割 name 和 value
        name, value = pair.split('=', 1)
        name = name.strip()
        value = value.strip()

        # URL 解码（如果需要）
        try:
            value = unquote(value)
        except:
            pass

        cookies[name] = value

    return cookies


def load_cookies(cookies_file: str) -> Dict[str, str]:
    """
    从文件加载 cookies，自动识别格式

    Args:
        cookies_file: cookies 文件路径

    Returns:
        Dict[str, str]: cookie 字典

    Raises:
        FileNotFoundError: 文件不存在
        Exception: 解析失败
    """
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            raise Exception("cookies 文件为空")

        # 尝试解析为 JSON
        try:
            cookies_data = json.loads(content)

            # 如果是字典，直接返回
            if isinstance(cookies_data, dict):
                logger.info(f"成功加载 JSON 格式 cookies，共 {len(cookies_data)} 个")
                return cookies_data
            else:
                raise Exception("JSON 格式不正确，应该是一个对象")

        except json.JSONDecodeError:
            # 不是 JSON 格式，尝试解析为 cookie 字符串
            logger.info("检测到 cookie 字符串格式，开始解析...")
            cookies = parse_cookie_string(content)
            logger.info(f"成功解析 cookie 字符串，共 {len(cookies)} 个")
            return cookies

    except FileNotFoundError:
        logger.error(f"cookies 文件不存在: {cookies_file}")
        raise FileNotFoundError(f"cookies 文件不存在: {cookies_file}")
    except Exception as e:
        logger.error(f"加载 cookies 失败: {str(e)}")
        raise Exception(f"加载 cookies 失败: {str(e)}")


def save_cookies_as_json(cookies: Dict[str, str], output_file: str):
    """
    将 cookies 保存为 JSON 格式

    Args:
        cookies: cookie 字典
        output_file: 输出文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    logger.info(f"cookies 已保存为 JSON 格式: {output_file}")
