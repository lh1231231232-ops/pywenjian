import time
import datetime

def check_vscode_time():
    print("=" * 40)
    print("🕒 VS Code (Python) 时间环境检测")
    print("=" * 40)

    # 1. 获取当前时间
    now = datetime.datetime.now()
    print(f"📅 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # 2. 获取本地时区名称
    # 如果伪装成功，这里应该显示 'Pacific Standard Time' 或类似的美国时区名
    # 如果显示 'China Standard Time'，说明伪装未生效
    try:
        timezone_name = time.tzname
        print(f"🌍 当前时区: {timezone_name}")
    except:
        print("🌍 当前时区: 无法获取")

    # 3. 计算与 UTC 的偏差（辅助验证）
    # 北京时间是 UTC+8，美国太平洋时间通常是 UTC-8 (冬令时) 或 UTC-7 (夏令时)
    # time.timezone 返回的是秒数，负数表示东区，正数表示西区（这是Python的一个怪癖）
    offset_hours = time.timezone / 3600
    print(f"⚡ UTC 偏差:  {offset_hours} 小时 (正数代表西区/美国，负数代表东区/中国)")
    
    print("-" * 40)
    
    # 判定结论
    if "China" in str(timezone_name) or offset_hours < 0:
        print("❌ 结果：检测到【北京时间/东八区】。")
        print("👉 原因：你可能没有通过 .bat 脚本启动 VS Code，或者是直接点击的任务栏图标。")
    elif "Pacific" in str(timezone_name) or "America" in str(timezone_name) or offset_hours > 0:
        print("✅ 结果：检测到【美国时间】！")
        print("🎉 恭喜：VS Code 认为自己在太平洋对岸。伪装成功。")
    else:
        print("⚠️ 结果：未知时区，请人工核对时间。")

if __name__ == "__main__":
    check_vscode_time()