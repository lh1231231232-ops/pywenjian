"""
爬取网易新闻，每日热文
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime
import re


def crawl_163_news():
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    url = 'https://news.163.com/domestic/'

    try:
        # 发送HTTP请求
        print("正在获取网易新闻页面...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # 检查请求是否成功

        # 设置正确的编码
        response.encoding = 'utf-8'

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找今日推荐HOT部分
        hot_recommendations = []

        # 方法1: 查找包含"今日推荐"或"HOT"标题的部分
        hot_titles = soup.find_all(['h2', 'h3', 'div'], string=re.compile(r'今日推荐|HOT|热门推荐'))

        for title_element in hot_titles:
            # 找到相邻的ul列表或包含链接的容器
            container = title_element.find_parent('div')
            if container:
                # 在容器中查找所有链接
                links = container.find_all('a', href=True)
                for link in links:
                    title = link.get_text().strip()
                    href = link['href']
                    if title and href and len(title) > 5:  # 过滤掉过短的标题（可能是无关链接）
                        # 确保链接是有效的新闻链接
                        if href.startswith('http') and ('news.163.com' in href or 'www.163.com' in href):
                            hot_recommendations.append({
                                '标题': title,
                                '链接': href
                            })

        # 方法2: 如果上述方法找不到，尝试通过类名查找
        if not hot_recommendations:
            for ul in soup.find_all('ul', class_=lambda x: x and ('list' in x or 'cm' in x or 'news' in x)):
                for item in ul.find_all('a', href=True):
                    title = item.get_text().strip()
                    href = item['href']
                    if title and href and len(title) > 5:
                        if href.startswith('http') and ('news.163.com' in href or 'www.163.com' in href):
                            hot_recommendations.append({
                                '标题': title,
                                '链接': href
                            })

        # 去重
        seen = set()
        unique_recommendations = []
        for item in hot_recommendations:
            if item['链接'] not in seen:
                seen.add(item['链接'])
                unique_recommendations.append(item)

        # 保存结果到Excel文件
        if unique_recommendations:
            # 生成文件名：网易新闻+日期
            current_date = datetime.now().strftime("%Y%m%d")
            excel_filename = f"网易新闻_{current_date}.xlsx"

            # 创建DataFrame
            df = pd.DataFrame(unique_recommendations)

            # 保存到Excel
            df.to_excel(excel_filename, index=False, engine='openpyxl')

            print(f"成功爬取 {len(unique_recommendations)} 条今日推荐内容")
            print(f"结果已保存到: {os.path.abspath(excel_filename)}")

            # 打印前几条结果
            print("\n前5条推荐内容:")
            for i, item in enumerate(unique_recommendations[:5], 1):
                print(f"{i}. {item['标题']}")

        else:
            print("未找到今日推荐内容，可能需要更新选择器")
            # 打印页面结构以便调试
            debug_filename = f"debug_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"已保存页面结构到 {debug_filename} 供分析")

    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    print("开始爬取网易新闻今日推荐...")
    crawl_163_news()
    print("程序执行完毕!")
