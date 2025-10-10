#!/usr/bin/env python3
"""
CSDN文库文章下载和解析单元测试
使用cookie完成文章下载并提取完整内容
"""
import requests
import json
from bs4 import BeautifulSoup
import re
import urllib3
from typing import Dict, Optional, Tuple
from html import unescape as html_unescape
import markdown
from markdown.extensions import fenced_code, codehilite

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WenkuArticleDownloader:
    """CSDN文库文章下载器"""
    
    def __init__(self, cookies_file: str = "../cookies.json"):
        """初始化下载器"""
        self.cookies_file = cookies_file
        self.session = None
        self.cookies_dict = None
    
    def load_cookies(self) -> bool:
        """加载cookies文件"""
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                self.cookies_dict = json.load(f)
            print(f"✅ 成功加载cookies，共{len(self.cookies_dict)}个")
            return True
        except FileNotFoundError:
            print(f"❌ {self.cookies_file}文件不存在")
            return False
        except Exception as e:
            print(f"❌ 加载cookies失败: {str(e)}")
            return False
    
    def setup_session(self):
        """设置会话"""
        if not self.cookies_dict:
            if not self.load_cookies():
                return False
        
        self.session = requests.Session()
        
        # 设置cookies
        for name, value in self.cookies_dict.items():
            self.session.cookies.set(name, value, domain='.csdn.net')
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://wenku.csdn.net/',
        }
        self.session.headers.update(headers)
        
        return True
    
    def download_article(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        下载文章HTML
        
        Returns:
            (success, html_content)
        """
        print(f"\n📡 正在请求文库页面...")
        print(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=30, allow_redirects=True, verify=False)
            
            print(f"响应状态码: {response.status_code}")
            print(f"最终URL: {response.url}")
            print(f"响应大小: {len(response.content):,} 字节")
            
            if response.status_code != 200:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                return False, None
            
            return True, response.text
            
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False, None
    
    def extract_article_content(self, html: str) -> Dict:
        """
        从HTML中提取文章内容
        
        Returns:
            {
                'title': str,
                'content': str,
                'text_content': str,
                'publish_time': str,
                'view_count': str,
                'author': str,
                'has_vip_marker': bool,
                'full_html': str,  # 完整的原始HTML
            }
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = {}
        
        # 保存完整的原始HTML
        result['full_html'] = html
        
        # 1. 提取标题
        title_tag = soup.find('h1', class_='title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True)
        else:
            title_tag = soup.find('title')
            result['title'] = title_tag.text.strip() if title_tag else '未知标题'
        
        print(f"\n📄 文章标题: {result['title']}")
        
        # 2. 提取元数据
        data_items = soup.find_all('span', class_='data-item')
        result['publish_time'] = ''
        result['view_count'] = ''
        result['author'] = ''
        
        for item in data_items:
            text = item.get_text(strip=True)
            if '时间:' in text:
                result['publish_time'] = text.replace('时间:', '').strip()
            elif '浏览:' in text:
                result['view_count'] = text.replace('浏览:', '').strip()
        
        # 3. 检测VIP标记
        vip_text = soup.get_text()
        result['has_vip_marker'] = bool(re.search(r'VIP|会员|付费|解锁|阅读全文', vip_text))
        
        # 4. 提取主要内容（只提取真正的文章内容，不含"阅读全文"按钮）
        # 文库文章的结构:
        # <div class="article-box">
        #   <div class="header">标题和元信息</div>
        #   <div class="cont">
        #     <div class="content-view">
        #       <div class="htmledit_views markdown_views">真正的文章内容</div>
        #     </div>
        #     <div class="open">阅读全文按钮（需要移除）</div>
        #   </div>
        # </div>
        
        content_area = None
        
        # 优先查找htmledit_views或markdown_views（最精确的内容区域）
        content_area = soup.find('div', class_=lambda x: x and ('htmledit_views' in x or 'markdown_views' in x))
        
        if content_area:
            print(f"✅ 找到精确的文章内容区域: {content_area.get('class')}")
        else:
            # 备用：查找content-view然后移除open按钮
            content_view = soup.find('div', class_='content-view')
            if content_view:
                print(f"✅ 找到content-view区域")
                # 查找并移除"阅读全文"按钮
                open_btn = content_view.find_next_sibling('div', class_='open')
                if open_btn:
                    print(f"🗑️  移除'阅读全文'按钮")
                    open_btn.decompose()
                content_area = content_view
            else:
                print("⚠️  未找到明确的内容区域，使用article-box")
                content_area = soup.find('div', class_='article-box') or soup
        
        # 5. 获取HTML内容（保留原始格式）
        result['content'] = str(content_area)
        
        # 6. 获取纯文本内容（用于统计）
        # 临时移除脚本和样式仅用于文本提取
        temp_content = BeautifulSoup(str(content_area), 'html.parser')
        for script in temp_content.find_all(['script', 'style']):
            script.decompose()
        
        text_content = temp_content.get_text(separator='\n', strip=True)
        # 解码HTML实体
        text_content = html_unescape(text_content)
        # 清理多余空白
        text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
        result['text_content'] = text_content
        
        print(f"📊 内容统计:")
        print(f"   HTML长度: {len(result['content']):,} 字符")
        print(f"   文本长度: {len(result['text_content']):,} 字符")
        print(f"   发布时间: {result['publish_time'] or '未知'}")
        print(f"   浏览量: {result['view_count'] or '未知'}")
        print(f"   VIP标记: {'是' if result['has_vip_marker'] else '否'}")
        
        return result
    
    def save_to_file(self, content: Dict, output_file: str) -> bool:
        """保存内容到文件（保留原始格式，渲染Markdown）"""
        try:
            # 方式1: 保存完整的原始HTML（备份）
            original_file = output_file.replace('.html', '_original.html')
            with open(original_file, 'w', encoding='utf-8') as f:
                f.write(content['full_html'])
            print(f"✅ 原始HTML已保存到: {original_file}")
            
            # 方式2: 保存渲染后的可读版本（Markdown转HTML，代码高亮）
            with open(output_file, 'w', encoding='utf-8') as f:
                soup = BeautifulSoup(content['full_html'], 'html.parser')
                
                # 提取head中的CSS样式链接
                head_content = soup.find('head')
                css_links = []
                if head_content:
                    for link in head_content.find_all('link', rel='stylesheet'):
                        css_links.append(str(link))
                
                # 只提取htmledit_views/markdown_views区域（真正的文章内容）
                article_content = soup.find('div', class_=lambda x: x and ('htmledit_views' in x or 'markdown_views' in x))
                
                if not article_content:
                    # 备用方案：使用content-view但移除"阅读全文"按钮
                    content_view = soup.find('div', class_='content-view')
                    if content_view:
                        article_content = BeautifulSoup(str(content_view), 'html.parser')
                        for open_btn in article_content.find_all('div', class_='open'):
                            open_btn.decompose()
                
                if not article_content:
                    print("⚠️  未找到文章内容，使用原始内容")
                    article_content = soup.find('body') or soup
                
                # 获取Markdown文本内容
                markdown_text = article_content.get_text()
                
                # 使用markdown库渲染HTML（支持代码块、语法高亮）
                md = markdown.Markdown(extensions=[
                    'fenced_code',  # 支持```代码块
                    'codehilite',   # 代码语法高亮
                    'tables',       # 表格支持
                    'nl2br',        # 换行转<br>
                ])
                rendered_html = md.convert(markdown_text)
                
                print(f"🎨 Markdown渲染完成，HTML长度: {len(rendered_html)} 字符")
                
                # 构建完整的HTML文档（带代码高亮样式）
                html_output = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content.get("title", "文库文章")}</title>
    {chr(10).join(css_links)}
    <style>
        body {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #fff;
            line-height: 1.8;
            color: #333;
        }}
        .article-meta {{ 
            color: #666; 
            margin: 20px 0; 
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
            border-left: 4px solid #fc5531;
        }}
        .article-meta p {{ margin: 5px 0; }}
        h1 {{ 
            color: #333; 
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #fc5531;
        }}
        
        /* 代码块样式（GitHub风格） */
        pre {{ 
            background: #f6f8fa; 
            padding: 16px; 
            border-radius: 6px; 
            overflow-x: auto;
            border: 1px solid #d0d7de;
            font-size: 14px;
            line-height: 1.45;
            margin: 16px 0;
        }}
        code {{ 
            background: #f6f8fa; 
            padding: 3px 6px; 
            border-radius: 3px; 
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
            font-size: 85%;
            color: #24292f;
        }}
        pre code {{
            background: transparent;
            padding: 0;
            border-radius: 0;
            font-size: 14px;
            display: block;
        }}
        
        /* Pygments代码高亮样式 */
        .codehilite {{ background: #f6f8fa; border-radius: 6px; padding: 16px; margin: 16px 0; }}
        .codehilite pre {{ background: transparent; border: none; padding: 0; margin: 0; }}
        
        /* 语法高亮颜色 */
        .codehilite .c {{ color: #6a737d; font-style: italic; }} /* Comment */
        .codehilite .k {{ color: #d73a49; font-weight: bold; }} /* Keyword */
        .codehilite .s {{ color: #032f62; }} /* String */
        .codehilite .n {{ color: #24292f; }} /* Name */
        .codehilite .o {{ color: #d73a49; }} /* Operator */
        .codehilite .m {{ color: #005cc5; }} /* Number */
        .codehilite .p {{ color: #24292f; }} /* Punctuation */
        
        /* 表格样式 */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        table th, table td {{
            border: 1px solid #d0d7de;
            padding: 8px 12px;
            text-align: left;
        }}
        table th {{
            background: #f6f8fa;
            font-weight: 600;
        }}
        
        /* 段落和列表 */
        p {{ margin: 12px 0; }}
        ul, ol {{ margin: 12px 0; padding-left: 2em; }}
        li {{ margin: 4px 0; }}
        
        .article-content {{
            font-size: 16px;
            line-height: 1.8;
        }}
    </style>
</head>
<body>
    <h1>{content.get("title", "文库文章")}</h1>
    <div class="article-meta">
        <p>📅 发布时间: {content.get("publish_time", "未知")}</p>
        <p>👁️ 浏览量: {content.get("view_count", "未知")}</p>
    </div>
    <div class="article-content">
        {rendered_html}
    </div>
</body>
</html>'''
                
                f.write(html_output)
            
            print(f"✅ 格式化HTML已保存到: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 保存文件失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def download_and_parse(self, url: str, output_file: str = None) -> Optional[Dict]:
        """
        完整流程：下载并解析文章
        
        Returns:
            提取的文章内容字典，失败返回None
        """
        print("="*70)
        print("📚 CSDN文库文章下载和解析")
        print("="*70)
        
        # 1. 设置会话
        if not self.setup_session():
            return None
        
        # 2. 下载文章
        success, html = self.download_article(url)
        if not success or not html:
            return None
        
        # 3. 解析内容
        content = self.extract_article_content(html)
        
        # 4. 保存到文件
        if output_file:
            self.save_to_file(content, output_file)
        
        # 5. 显示内容预览
        preview_length = 500
        print(f"\n📖 内容预览 (前{preview_length}字符):")
        print("-"*70)
        preview = content['text_content'][:preview_length]
        print(preview)
        if len(content['text_content']) > preview_length:
            print("...")
        print("-"*70)
        
        return content


def test_wenku_download():
    """测试文库文章下载"""
    # 测试URL
    test_url = "https://wenku.csdn.net/answer/3pzv32zt84"
    
    # 创建下载器
    downloader = WenkuArticleDownloader()
    
    # 下载并解析
    result = downloader.download_and_parse(
        url=test_url,
        output_file="wenku_article_complete.html"
    )
    
    # 验证结果
    print("\n" + "="*70)
    if result:
        print("✅ 测试通过!")
        print(f"\n提取的信息:")
        print(f"  标题: {result['title']}")
        print(f"  发布时间: {result['publish_time'] or '未知'}")
        print(f"  浏览量: {result['view_count'] or '未知'}")
        print(f"  内容长度: {len(result['text_content']):,} 字符")
        print(f"  HTML长度: {len(result['content']):,} 字符")
        
        # 检查内容质量
        if len(result['text_content']) < 100:
            print("\n⚠️  警告: 提取的内容可能不完整")
        else:
            print("\n✅ 内容提取完整")
    else:
        print("❌ 测试失败")
    print("="*70)
    
    return result is not None


if __name__ == "__main__":
    # 运行测试
    success = test_wenku_download()
    
    # 返回测试结果
    exit(0 if success else 1)
