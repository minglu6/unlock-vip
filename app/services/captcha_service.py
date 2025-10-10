"""
验证码识别服务
支持多种第三方验证码识别平台
"""
import base64
import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
import requests


class CaptchaService:
    """验证码识别服务基类"""

    def recognize(self, image_path: str) -> Optional[List[Tuple[int, int]]]:
        """
        识别验证码

        Args:
            image_path: 验证码图片路径

        Returns:
            识别结果的坐标列表 [(x1, y1), (x2, y2), ...]
        """
        raise NotImplementedError


class ChaoJiYingService(CaptchaService):
    """超级鹰验证码识别服务"""

    def __init__(self, username: str, password: str, soft_id: str):
        """
        初始化超级鹰服务

        Args:
            username: 超级鹰用户名
            password: 超级鹰密码
            soft_id: 软件ID
        """
        self.username = username
        self.password = password
        self.soft_id = soft_id
        self.base_url = 'http://upload.chaojiying.net/Upload/Processing.php'

    def _md5(self, text: str) -> str:
        """计算MD5"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def recognize(self, image_path: str, code_type: int = 9004) -> Optional[List[Tuple[int, int]]]:
        """
        识别点击验证码

        Args:
            image_path: 验证码图片路径
            code_type: 验证码类型
                - 9004: 点选验证码（4个汉字）
                - 9005: 点选验证码（5个汉字）
                - 9006: 点选验证码（6个汉字）

        Returns:
            识别结果的坐标列表 [(x1, y1), (x2, y2), ...]
        """
        try:
            # 读取图片并转为base64
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode('utf-8')

            preview = image_data[:60] + ('...' if len(image_data) > 60 else '')
            print(
                f"[Upload] 超级鹰请求: user={self.username}, soft_id={self.soft_id}, code_type={code_type}, "
                f"image_bytes={len(image_bytes)}, base64_preview={preview}"
            )

            # 构建请求参数
            data = {
                'user': self.username,
                'pass2': self._md5(self.password),
                'softid': self.soft_id,
                'codetype': code_type,
                'file_base64': image_data,
            }

            # 发送识别请求
            print(f"[Processing] 正在识别验证码...")
            response = requests.post(self.base_url, data=data, timeout=30)
            result = response.json()
            print(f"[Receive] 超级鹰响应: {json.dumps(result, ensure_ascii=False)}")

            # 检查识别结果
            if result.get('err_no') == 0:
                # 解析坐标
                pic_str = result.get('pic_str', '')
                print(f"[OK] 验证码识别成功: {pic_str}")

                # 坐标格式: "x1,y1|x2,y2|x3,y3|x4,y4"
                coordinates: List[Tuple[int, int]] = []
                for coord_str in pic_str.split('|'):
                    coord_str = coord_str.strip()
                    if not coord_str:
                        continue

                    parts = coord_str.split(',')
                    if len(parts) != 2:
                        print(f"[WARN] 无效坐标格式: {coord_str}")
                        continue

                    try:
                        x, y = map(int, parts)
                    except ValueError:
                        print(f"[WARN] 坐标解析失败: {coord_str}")
                        continue

                    coordinates.append((x, y))

                if not coordinates:
                    print("[WARN] 验证码识别成功但未返回坐标")

                return coordinates
            else:
                error_msg = result.get('err_str', '未知错误')
                print(f"[ERROR] 验证码识别失败: {error_msg}")
                return None

        except Exception as e:
            print(f"[ERROR] 验证码识别异常: {str(e)}")
            return None

    def report_error(self, pic_id: str) -> bool:
        """
        报告识别错误（用于退款）

        Args:
            pic_id: 图片ID（从识别结果中获取）

        Returns:
            是否报告成功
        """
        try:
            data = {
                'user': self.username,
                'pass2': self._md5(self.password),
                'softid': self.soft_id,
                'id': pic_id,
            }

            response = requests.post(
                'http://upload.chaojiying.net/Upload/ReportError.php',
                data=data,
                timeout=10
            )
            result = response.json()

            return result.get('err_no') == 0
        except:
            return False


class TwoCaptchaService(CaptchaService):
    """2Captcha验证码识别服务（国际服务）"""

    def __init__(self, api_key: str):
        """
        初始化2Captcha服务

        Args:
            api_key: API密钥
        """
        self.api_key = api_key
        self.base_url = 'http://2captcha.com'

    def recognize(self, image_path: str) -> Optional[List[Tuple[int, int]]]:
        """
        识别点击验证码

        Args:
            image_path: 验证码图片路径

        Returns:
            识别结果的坐标列表 [(x1, y1), (x2, y2), ...]
        """
        try:
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # 提交识别任务
            print(f"🔍 正在提交验证码识别任务...")
            files = {'file': image_data}
            data = {
                'key': self.api_key,
                'method': 'post',
            }

            response = requests.post(
                f'{self.base_url}/in.php',
                files=files,
                data=data,
                timeout=30
            )

            if 'OK|' not in response.text:
                print(f"[ERROR] 提交失败: {response.text}")
                return None

            captcha_id = response.text.split('|')[1]
            print(f"[OK] 任务已提交，ID: {captcha_id}")

            # 等待识别结果
            for i in range(60):
                time.sleep(3)
                result_response = requests.get(
                    f'{self.base_url}/res.php',
                    params={
                        'key': self.api_key,
                        'action': 'get',
                        'id': captcha_id,
                    },
                    timeout=10
                )

                if 'OK|' in result_response.text:
                    result = result_response.text.split('|')[1]
                    print(f"[OK] 验证码识别成功: {result}")

                    # 解析坐标
                    coordinates = []
                    for coord_str in result.split(','):
                        parts = coord_str.split(':')
                        if len(parts) == 2:
                            x, y = map(int, parts)
                            coordinates.append((x, y))

                    return coordinates
                elif 'CAPCHA_NOT_READY' in result_response.text:
                    continue
                else:
                    print(f"[ERROR] 识别失败: {result_response.text}")
                    return None

            print("[ERROR] 识别超时")
            return None

        except Exception as e:
            print(f"[ERROR] 验证码识别异常: {str(e)}")
            return None


class MockCaptchaService(CaptchaService):
    """模拟验证码识别服务（用于测试）"""

    def recognize(self, image_path: str) -> Optional[List[Tuple[int, int]]]:
        """
        模拟识别（返回固定坐标）

        Args:
            image_path: 验证码图片路径

        Returns:
            模拟的坐标列表
        """
        print("[Mock] 使用模拟识别服务...")
        print("[WARN] 这是测试模式，返回的是固定坐标，实际使用请配置真实的验证码服务")

        # 返回示例坐标
        return [(100, 100), (200, 150), (150, 200), (250, 120)]


def get_captcha_service(service_type: str = 'chaojiying', **kwargs) -> CaptchaService:
    """
    获取验证码识别服务

    Args:
        service_type: 服务类型 ('chaojiying', '2captcha', 'mock')
        **kwargs: 服务配置参数

    Returns:
        验证码识别服务实例
    """
    if service_type == 'chaojiying':
        return ChaoJiYingService(
            username=kwargs.get('username', ''),
            password=kwargs.get('password', ''),
            soft_id=kwargs.get('soft_id', ''),
        )
    elif service_type == '2captcha':
        return TwoCaptchaService(
            api_key=kwargs.get('api_key', ''),
        )
    elif service_type == 'mock':
        return MockCaptchaService()
    else:
        raise ValueError(f"不支持的验证码服务类型: {service_type}")