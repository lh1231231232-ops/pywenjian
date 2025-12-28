import datetime


def check_vscode_time():
    print("=" * 40)
    print("🕒 VS Code (Python) 时间环境检测")
    print("=" * 40)

    # 读取当前本地时间，便于人工比对显示是否正常
    now = datetime.datetime.now()
    print(f"📅 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # Use astimezone() to get a more reliable local TZ name and offset.
    try:
        local_dt = datetime.datetime.now().astimezone()
        timezone_name = local_dt.tzname() or ""
        print(f"🌍 当前时区: {timezone_name}")
        offset = local_dt.utcoffset()
    except Exception:
        timezone_name = ""
        offset = None
        print("🌍 当前时区: 无法获取")

    # 将 UTC 偏移转成小时，避免 time.timezone 的正负混淆
    if offset is not None:
        offset_hours = offset.total_seconds() / 3600
        print(f"⚡ UTC 偏移: {offset_hours} 小时")
    else:
        offset_hours = None
        print("⚡ UTC 偏移: 无法获取")

    print("-" * 40)

    # 根据时区名或 UTC 偏移做一个粗略判断
    if "China" in timezone_name or (offset_hours is not None and offset_hours >= 7.5):
        print("❌ 结果：检测到【北京时间/东八区】")
        print("👉 原因：可能未通过 .bat 脚本启动 VS Code，或直接点击了任务栏图标。")
    elif (
        "Pacific" in timezone_name
        or "America" in timezone_name
        or (offset_hours is not None and offset_hours <= -7.0)
    ):
        print("✅ 结果：检测到【美国时间】")
        print("🎉 恭喜：VS Code 认为自己在太平洋对岸，伪装成功。")
    else:
        print("⚠️ 结果：未知时区，请人工核对时间。")


if __name__ == "__main__":
    check_vscode_time()
