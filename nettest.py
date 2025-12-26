import urllib.request
import json
import socket
import os

# 配置你的 Clash 端口 (通常是 7890)
PROXY_PORT = 7897
PROXY_URL = f'http://127.0.0.1:{PROXY_PORT}'

def get_ip_info(use_proxy=False):
    url = 'https://api.ipify.org?format=json'
    # 备用 API (显示更多信息): 'http://ip-api.com/json' 
    
    try:
        if use_proxy:
            # 设置代理 Handler
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY_URL, 'https': PROXY_URL})
            opener = urllib.request.build_opener(proxy_handler)
            print(f"🔄 正在通过代理 ({PROXY_URL}) 请求...")
        else:
            # 不使用代理 (直连)
            opener = urllib.request.build_opener()
            print("🔄 正在尝试直连请求 (测试本地 IP)...")
            
        # 发送请求
        response = opener.open(url, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        return data['ip']
    except Exception as e:
        return f"请求失败: {str(e)}"

if __name__ == "__main__":
    print("="*30)
    print(" 🕵️  IP 验证工具")
    print("="*30)

    # 1. 测试当前环境（可能走系统代理，也可能直连）
    # 如果你在 VS Code 终端里设置了 export http_proxy... 这里会显示代理 IP
    current_ip = get_ip_info(use_proxy=False)
    print(f"👉 当前环境 IP: {current_ip}")
    print("-" * 30)

    # 2. 强制指定走 Clash 端口
    # 这能验证你的代理软件是否通畅，以及最终出口 IP
    proxy_ip = get_ip_info(use_proxy=True)
    print(f"👉 强制代理 IP: {proxy_ip}")
    print("="*30)
    
    # 简单判断
    if proxy_ip == current_ip:
        print("💡 提示: 两次 IP 相同。")
    else:
        print("💡 提示: 代理已生效，IP 不同。")
        print("请核对 '强制代理 IP' 是否为你购买的【美国静态 IP】。")