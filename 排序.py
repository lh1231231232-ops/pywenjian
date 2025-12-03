def sort_coordinates(coords):
    # 提取所有纬度和经度
    latitudes = [coord[0] for coord in coords]
    longitudes = [coord[1] for coord in coords]
    
    # 计算最小/最大纬度和经度
    min_lat = min(latitudes)
    max_lat = max(latitudes)
    min_lon = min(longitudes)
    max_lon = max(longitudes)
    
    return min_lat, min_lon, max_lat, max_lon

# 示例输入（四个经纬度点）
coordinates = [
    (96.04694940, 29.50138005),  # 北京
    (96.04032821, 29.49445191),  # 上海
]

# 调用函数并输出结果
min_lat, min_lon, max_lat, max_lon = sort_coordinates(coordinates)
print(f"最小纬度: {min_lat}")
print(f"最小经度: {min_lon}")
print(f"最大纬度: {max_lat}")
print(f"最大经度: {max_lon}")

# 输出格式化为一行（按题目要求顺序）
print(f"{min_lat} {min_lon} {max_lat} {max_lon}")