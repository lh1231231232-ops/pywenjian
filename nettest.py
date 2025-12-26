# import urllib.request
# import json
# import socket
# import os

# # 配置你的 Clash 端口 (通常是 7890)
# PROXY_PORT = 7897
# PROXY_URL = f'http://127.0.0.1:{PROXY_PORT}'

# def get_ip_info(use_proxy=False):
#     url = 'https://api.ipify.org?format=json'
#     # 备用 API (显示更多信息): 'http://ip-api.com/json' 
    
#     try:
#         if use_proxy:
#             # 设置代理 Handler
#             proxy_handler = urllib.request.ProxyHandler({'http': PROXY_URL, 'https': PROXY_URL})
#             opener = urllib.request.build_opener(proxy_handler)
#             print(f"🔄 正在通过代理 ({PROXY_URL}) 请求...")
#         else:
#             # 不使用代理 (直连)
#             opener = urllib.request.build_opener()
#             print("🔄 正在尝试直连请求 (测试本地 IP)...")
            
#         # 发送请求
#         response = opener.open(url, timeout=10)
#         data = json.loads(response.read().decode('utf-8'))
#         return data['ip']
#     except Exception as e:
#         return f"请求失败: {str(e)}"

# if __name__ == "__main__":
#     print("="*30)
#     print(" 🕵️  IP 验证工具")
#     print("="*30)

#     # 1. 测试当前环境（可能走系统代理，也可能直连）
#     # 如果你在 VS Code 终端里设置了 export http_proxy... 这里会显示代理 IP
#     current_ip = get_ip_info(use_proxy=False)
#     print(f"👉 当前环境 IP: {current_ip}")
#     print("-" * 30)

#     # 2. 强制指定走 Clash 端口
#     # 这能验证你的代理软件是否通畅，以及最终出口 IP
#     proxy_ip = get_ip_info(use_proxy=True)
#     print(f"👉 强制代理 IP: {proxy_ip}")
#     print("="*30)
    
#     # 简单判断
#     if proxy_ip == current_ip:
#         print("💡 提示: 两次 IP 相同。")
#     else:
#         print("💡 提示: 代理已生效，IP 不同。")
#         print("请核对 '强制代理 IP' 是否为你购买的【美国静态 IP】。")

import urllib.request
import json
import os
import sys

# ---------------- 配置区域 ----------------
# 请查看 Clash Verge 设置界面的 "Service Port" 或 "Mixed Port"
# 新版默认通常是 7897，旧版是 7890
PROXY_PORT = 7897 
# ----------------------------------------

def check_ip():
    print("="*40)
    print("🚀 开始网络环境检测...")
    
    # 1. 构造代理地址
    proxy_url = f'http://127.0.0.1:{PROXY_PORT}'
    print(f"📡 目标代理端口: {PROXY_PORT}")

    # 2. 设置代理处理器
    proxy_handler = urllib.request.ProxyHandler({
        'http': proxy_url,
        'https': proxy_url
    })
    opener = urllib.request.build_opener(proxy_handler)
    
    # 3. 发起请求
    try:
        print("⏳ 正在连接 ip-api.com 查询 IP...")
        # 这个 API 会返回详细的地理位置信息
        req = urllib.request.Request(
            'http://ip-api.com/json/?fields=status,message,country,city,query,isp', 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = opener.open(req, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        
        print("-" * 40)
        if data['status'] == 'success':
            print(f"✅ 连接成功！")
            print(f"🌍 当前 IP:   {data['query']}")
            print(f"🏳️  国家/城市: {data['country']} - {data['city']}")
            print(f"🏢 运营商:     {data['isp']}")
            print("-" * 40)
            print("📝 结果分析：")
            if data['country'] == 'United States':
                print("🎉 完美！检测到美国 IP。你的伪装已生效。")
            elif data['country'] == 'China':
                print("❌ 警告！检测到中国 IP。代理未生效，请检查端口号或Clash开关。")
            else:
                print(f"⚠️ 注意！检测到 {data['country']} IP。")
                print("如果是香港/日本，说明走了普通机场节点，没走静态专线。")
                print("(如果你的规则只写了 code.exe，请记得把 python.exe 也加入规则)")
        else:
            print("❌ API 返回错误")
            
    except urllib.error.URLError as e:
        print("❌ 连接失败！")
        print(f"错误原因: {e.reason}")
        print("👉 请检查：")
        print(f"1. Clash Verge 是否已启动？")
        print(f"2. 脚本中的端口 {PROXY_PORT} 是否与 Clash 设置一致？")
        print(f"3. 是否开启了 System Proxy (系统代理)？")

if __name__ == "__main__":
    check_ip()