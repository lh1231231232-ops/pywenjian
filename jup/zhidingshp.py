import os
import glob
import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import traceback
import psutil
import re
import matplotlib
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
from pyproj import CRS
import geopandas as gpd
from shapely.geometry import box

# 设置matplotlib后端以避免PyCharm兼容性问题
matplotlib.use('TkAgg')  # 使用Tkinter作为后端

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']

# 1. 设置路径
base_path = r"D:\liaotianwenian\xwechat_files\wxid_arsup2052o6922_81c9\msg\file\2025-09\219多期遥感影像\2024-2025\2024.08-1"

# 2. 让用户输入目标区域的经纬度范围或选择shp文件
def get_target_bounds():
    print("\n请选择目标区域定义方式:")
    print("1. 手动输入经纬度范围")
    print("2. 从shp文件中读取范围")
    
    while True:
        try:
            choice = input("请输入选择 (1 或 2): ").strip()
            
            if choice == "1":
                print("\n请设置目标区域的经纬度范围")
                print("格式：最小经度 最小纬度 最大经度 最大纬度")
                print("示例：73.5 37.5 76.5 40.5 (喀什地区)")
                
                while True:
                    try:
                        input_str = input("请输入经纬度范围（或按Enter使用默认喀什地区范围）: ").strip()
                        
                        if not input_str:
                            # 使用默认喀什地区范围
                            return [73.5, 37.5, 76.5, 40.5], "手动输入范围"
                        
                        values = [float(x) for x in input_str.split()]
                        
                        if len(values) != 4:
                            print("错误：需要输入4个数值")
                            continue
                            
                        min_lon, min_lat, max_lon, max_lat = values
                        
                        # 验证范围
                        if min_lon >= max_lon or min_lat >= max_lat:
                            print("错误：最小经度应小于最大经度，最小纬度应小于最大纬度")
                            continue
                            
                        if min_lon < -180 or max_lon > 180 or min_lat < -90 or max_lat > 90:
                            print("错误：经度范围应在-180到180之间，纬度范围应在-90到90之间")
                            continue
                            
                        return [min_lon, min_lat, max_lon, max_lat], "手动输入范围"
                        
                    except ValueError:
                        print("错误：请输入有效的数字")
                    except Exception as e:
                        print(f"输入错误: {e}")
            
            elif choice == "2":
                print("\n请提供shp文件路径")
                while True:
                    shp_path = input("请输入shp文件完整路径: ").strip()
                    
                    if not os.path.exists(shp_path):
                        print("错误：文件不存在，请重新输入")
                        continue
                    
                    try:
                        # 读取shp文件
                        gdf = gpd.read_file(shp_path)
                        
                        # 显示可用的字段
                        print(f"\nshp文件包含以下字段: {list(gdf.columns)}")
                        
                        # 询问用户使用哪个字段来选择区域
                        field_name = input("请输入用于选择区域的字段名称: ").strip()
                        
                        if field_name not in gdf.columns:
                            print(f"错误：字段 '{field_name}' 不存在于shp文件中")
                            continue
                        
                        # 显示该字段的所有唯一值
                        unique_values = gdf[field_name].unique()
                        print(f"\n字段 '{field_name}' 包含以下值:")
                        for i, value in enumerate(unique_values):
                            print(f"{i+1}. {value}")
                        
                        # 让用户选择特定区域
                        try:
                            selection = input("\n请输入要选择的区域编号或名称: ").strip()
                            
                            # 尝试按编号选择
                            if selection.isdigit():
                                idx = int(selection) - 1
                                if 0 <= idx < len(unique_values):
                                    selected_value = unique_values[idx]
                                else:
                                    print("错误：编号超出范围")
                                    continue
                            else:
                                # 按名称选择
                                selected_value = selection
                                if selected_value not in unique_values:
                                    print(f"错误：'{selected_value}' 不在可用值中")
                                    continue
                            
                            # 筛选出选定的区域
                            selected_gdf = gdf[gdf[field_name] == selected_value]
                            
                            # 获取选定区域的总体范围
                            total_bounds = selected_gdf.total_bounds
                            
                            # 如果是地理坐标系，直接使用
                            if selected_gdf.crs and selected_gdf.crs.is_geographic:
                                min_lon, min_lat, max_lon, max_lat = total_bounds
                                print(f"从shp文件中读取的区域 '{selected_value}' 的范围: {min_lon}, {min_lat}, {max_lon}, {max_lat}")
                                return [min_lon, min_lat, max_lon, max_lat], f"shp区域: {selected_value}"
                            else:
                                # 如果不是地理坐标系，转换为WGS84 (EPSG:4326)
                                selected_gdf_wgs84 = selected_gdf.to_crs(epsg=4326)
                                total_bounds = selected_gdf_wgs84.total_bounds
                                min_lon, min_lat, max_lon, max_lat = total_bounds
                                print(f"从shp文件中读取并转换为WGS84的区域 '{selected_value}' 的范围: {min_lon}, {min_lat}, {max_lon}, {max_lat}")
                                return [min_lon, min_lat, max_lon, max_lat], f"shp区域: {selected_value}"
                                
                        except Exception as e:
                            print(f"选择区域时出错: {e}")
                            continue
                            
                    except Exception as e:
                        print(f"读取shp文件时出错: {e}")
                        print("请检查文件格式是否正确")
                        continue
            
            else:
                print("错误：请输入1或2")
                
        except Exception as e:
            print(f"输入错误: {e}")

# 获取用户输入的目标区域
TARGET_BOUNDS, AREA_DESCRIPTION = get_target_bounds()
print(f"目标区域设置为: {TARGET_BOUNDS}")
print(f"区域描述: {AREA_DESCRIPTION}")

# 获取输出文件名和图表标题
def get_output_settings(area_description):
    print("\n请设置输出文件的名称")
    print("注意：不要包含文件扩展名，程序会自动添加")
    
    while True:
        csv_name = input("请输入CSV文件名（或按Enter使用默认'snow_cover_timeseries'）: ").strip()
        plot_name = input("请输入折线图文件名（或按Enter使用默认'snow_cover_timeseries_plot'）: ").strip()
        plot_title = input("请输入折线图标题（或按Enter使用默认标题）: ").strip()
        
        # 设置默认值
        if not csv_name:
            csv_name = "snow_cover_timeseries"
        if not plot_name:
            plot_name = "snow_cover_timeseries_plot"
        if not plot_title:
            plot_title = f'Sentinel-2 积雪覆盖时间序列\n{area_description}'
        
        # 验证文件名是否合法
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        if any(char in csv_name for char in invalid_chars) or any(char in plot_name for char in invalid_chars):
            print("错误：文件名包含非法字符（\\ / : * ? \" < > |），请重新输入")
            continue
            
        return csv_name, plot_name, plot_title

# 获取雪深最大值
def get_snow_depth_max():
    print("\n请设置雪深最大值（当积雪覆盖率为100%时对应的雪深值）")
    print("单位：米")
    print("示例：3.5 (表示当积雪覆盖率为100%时，雪深为3.5米)")
    
    while True:
        try:
            input_str = input("请输入雪深最大值（或按Enter使用默认值3.5米）: ").strip()
            
            if not input_str:
                # 使用默认值
                return 3.5
                
            value = float(input_str)
            
            if value <= 0:
                print("错误：雪深最大值必须大于0")
                continue
                
            return value
            
        except ValueError:
            print("错误：请输入有效的数字")
        except Exception as e:
            print(f"输入错误: {e}")

# 获取雪深最大值
SNOW_DEPTH_MAX = get_snow_depth_max()
print(f"雪深最大值设置为: {SNOW_DEPTH_MAX}米")

# 获取输出设置
CSV_FILENAME, PLOT_FILENAME, PLOT_TITLE = get_output_settings(AREA_DESCRIPTION)
print(f"CSV文件将保存为: {CSV_FILENAME}.csv")
print(f"折线图将保存为: {PLOT_FILENAME}.png")
print(f"折线图标题设置为: {PLOT_TITLE}")

# 3. 自动发现所有可用的影像数据
safe_folders = glob.glob(os.path.join(base_path, "*.SAFE"))
print(f"发现 {len(safe_folders)} 个 Sentinel-2 数据集")

# 用于存储结果的列表
results = []

# 4. 遍历处理每一景影像
total = len(safe_folders)
processed = 0

for folder in safe_folders:
    processed += 1
    try:
        print(f"\n处理影像 ({processed}/{total}): {os.path.basename(folder)}")
        print(f"内存使用: {psutil.virtual_memory().percent}%")
        
        # 4.1 从文件夹名称中提取日期
        folder_name = os.path.basename(folder)
        
        # 使用正则表达式提取日期
        match = re.search(r'(\d{4})[\.\-]?(\d{2})[\.\-]?(\d{2})', folder_name)
        if match:
            year, month, day = match.groups()
            date_str = f"{year}{month}{day}"
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                print(f"警告: 日期格式无效 {date_str}，尝试使用默认日期")
                date_obj = datetime.now()
        else:
            # 尝试从标准Sentinel-2命名格式中提取日期
            parts = folder_name.split('_')
            if len(parts) >= 3:
                date_str = parts[2][:8]  # 例如 '20230101T100101' -> '20230101'
                try:
                    date_obj = datetime.strptime(date_str, "%Y%m%d")
                except (ValueError, IndexError):
                    print(f"警告: 无法从文件夹名 {folder_name} 中提取日期，使用默认日期")
                    date_obj = datetime.now()
            else:
                print(f"警告: 无法从文件夹名 {folder_name} 中提取日期，使用默认日期")
                date_obj = datetime.now()
        
        print(f"处理日期: {date_obj.strftime('%Y-%m-%d')}")

        # 4.2 查找波段文件
        band_b3_path = None
        band_b11_path = None
        
        # 可能的波段文件路径模式
        b3_patterns = [
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R10m', '*_B03_10m.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*_B03_20m.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B03_*.jp2'),
            # L1C产品中的路径
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*_B03_*.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R10m', '*.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*.jp2'),
            # L1C产品中的路径 - 精确匹配您提供的文件名格式
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'T*_B03.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B03.jp2'),
            # 尝试匹配任何位置下的B03文件
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*B03*.jp2'),
            # 如果以上都没有，尝试在更深的目录中查找
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*', '*B03*.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*', '*B03.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*B03.jp2')
            
        ]
        
        b11_patterns = [
            # L2A产品中的路径
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*_B11_20m.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B11_*.jp2'),
            # L1C产品中的路径
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*_B11_*.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*.jp2'),
            # L1C产品中的路径 - 精确匹配您提供的文件名格式
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'T*_B11.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B11.jp2'),
            # 尝试匹配任何位置下的B11文件
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*B11*.jp2'),
            # 如果以上都没有，尝试在更深的目录中查找
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*', '*B11*.jp2')
        ]
        
        # 尝试查找绿光波段 (B3)
        for pattern in b3_patterns:
            band_b3_list = glob.glob(pattern)
            if band_b3_list:
                band_b3_path = band_b3_list[0]
                break
        
        # 尝试查找短波红外波段 (B11)
        for pattern in b11_patterns:
            band_b11_list = glob.glob(pattern)
            if band_b11_list:
                band_b11_path = band_b11_list[0]
                break
        
        # 检查是否找到波段文件
        if not band_b3_path:
            print(f"错误: 在 {folder} 中未找到绿光波段 (B03) 文件，跳过")
            continue
            
        if not band_b11_path:
            print(f"错误: 在 {folder} 中未找到短波红外波段 (B11) 文件，跳过")
            continue
            
        print(f"使用绿光波段: {band_b3_path}")
        print(f"使用短波红外波段: {band_b11_path}")

        # 4.3 打开波段并裁剪到目标区域
        try:
            with rasterio.open(band_b3_path) as src_b3:
                # 将目标区域从WGS84转换到影像的CRS
                if src_b3.crs != CRS.from_epsg(4326):
                    transformed_bounds = transform_bounds(
                        CRS.from_epsg(4326), 
                        src_b3.crs, 
                        TARGET_BOUNDS[0], TARGET_BOUNDS[1], 
                        TARGET_BOUNDS[2], TARGET_BOUNDS[3]
                    )
                else:
                    transformed_bounds = TARGET_BOUNDS
                
                # 替换原有的窗口创建代码
                try:
                    # 尝试使用from_bounds创建窗口
                    window = from_bounds(
                        transformed_bounds[0], transformed_bounds[1],
                        transformed_bounds[2], transformed_bounds[3],
                        transform=src_b3.transform
                    )
                    
                    # 确保窗口在图像范围内
                    window = window.intersection((0, 0, src_b3.height, src_b3.width))
                    
                    if window.height == 0 or window.width == 0:
                        print("目标区域在影像范围之外，跳过")
                        continue
                    
                    green = src_b3.read(1, window=window).astype(np.float32)
                    profile = src_b3.profile
                    transform_cropped = src_b3.window_transform(window)
                except Exception as e:
                    print(f"使用from_bounds创建窗口失败: {e}")
                    # 使用更稳健的替代方法
                    try:
                        # 计算像素坐标
                        row_min, col_min = src_b3.index(transformed_bounds[0], transformed_bounds[3])
                        row_max, col_max = src_b3.index(transformed_bounds[2], transformed_bounds[1])
                        
                        # 确保坐标在图像范围内
                        row_min = max(0, row_min)
                        row_max = min(src_b3.height, row_max)
                        col_min = max(0, col_min)
                        col_max = min(src_b3.width, col_max)
                        
                        if row_min >= row_max or col_min >= col_max:
                            print("目标区域在影像范围之外，跳过")
                            continue
                        
                        # 创建窗口
                        window = ((row_min, row_max), (col_min, col_max))
                        
                        # 读取数据
                        green = src_b3.read(1, window=window).astype(np.float32)
                        profile = src_b3.profile
                        transform_cropped = src_b3.window_transform(window)
                    except Exception as e2:
                        print(f"替代方法也失败: {e2}")
                        continue
        except Exception as e:
            print(f"打开绿光波段失败: {e}")
            continue
            
        try:
            with rasterio.open(band_b11_path) as src_b11:
                # 将目标区域从WGS84转换到影像的CRS
                if src_b11.crs != CRS.from_epsg(4326):
                    transformed_bounds_b11 = transform_bounds(
                        CRS.from_epsg(4326), 
                        src_b11.crs, 
                        TARGET_BOUNDS[0], TARGET_BOUNDS[1], 
                        TARGET_BOUNDS[2], TARGET_BOUNDS[3]
                    )
                else:
                    transformed_bounds_b11 = TARGET_BOUNDS
                
                # 创建窗口裁剪数据 - 修复错误
                try:
                    # 尝试使用from_bounds创建窗口
                    window_b11 = from_bounds(
                        transformed_bounds_b11[0], transformed_bounds_b11[1],
                        transformed_bounds_b11[2], transformed_bounds_b11[3],
                        transform=src_b11.transform
                    )
                    
                    # 确保窗口在图像范围内
                    window_b11 = window_b11.intersection((0, 0, src_b11.height, src_b11.width))
                    
                    if window_b11.height == 0 or window_b11.width == 0:
                        print("目标区域在B11影像范围之外，跳过")
                        continue
                    
                    swir = src_b11.read(1, window=window_b11).astype(np.float32)
                    transform_b11_cropped = src_b11.window_transform(window_b11)
                except Exception as e:
                    print(f"使用from_bounds创建窗口失败: {e}")
                    # 使用替代方法：直接读取整个图像然后裁剪
                    print("尝试使用替代方法裁剪...")
                    # 计算像素坐标
                    row_min, col_min = src_b11.index(transformed_bounds_b11[0], transformed_bounds_b11[3])
                    row_max, col_max = src_b11.index(transformed_bounds_b11[2], transformed_bounds_b11[1])
                    
                    # 确保坐标在图像范围内
                    row_min = max(0, row_min)
                    row_max = min(src_b11.height, row_max)
                    col_min = max(0, col_min)
                    col_max = min(src_b11.width, col_max)
                    
                    if row_min >= row_max or col_min >= col_max:
                        print("目标区域在影像范围之外，跳过")
                        continue
                    
                    # 创建窗口
                    window_b11 = ((row_min, row_max), (col_min, col_max))
                    
                    # 读取数据
                    swir = src_b11.read(1, window=window_b11).astype(np.float32)
                    transform_b11_cropped = src_b11.window_transform(window_b11)
                
                # 使用rasterio进行重采样（如果分辨率不同）
                if green.shape != swir.shape:
                    print(f"分辨率不同: 绿光波段 {green.shape}, 短波红外波段 {swir.shape}, 进行重采样")
                    swir_resized = np.empty_like(green)
                    reproject(
                        swir,
                        swir_resized,
                        src_transform=transform_b11_cropped,
                        src_crs=src_b11.crs,
                        dst_transform=transform_cropped,
                        dst_crs=profile['crs'],
                        resampling=Resampling.bilinear
                    )
                    swir = swir_resized
        except Exception as e:
            print(f"打开短波红外波段失败: {e}")
            continue

        # 4.4 计算NDSI（归一化差分雪指数）
        np.seterr(divide='ignore', invalid='ignore')  # 忽略除以零的警告
        ndsi = (green - swir) / (green + swir)

        # 4.5 创建积雪掩膜 (NDSI > 0.4 通常被认为是雪)
        snow_mask = ndsi > 0.4

        # 4.6 计算积雪像素占总像素的比例
        valid_pixels = ~np.isnan(ndsi)  # 忽略NaN值
        total_pixels = np.sum(valid_pixels)
        
        if total_pixels == 0:
            print(f"警告: 没有有效像素，跳过")
            continue
            
        snow_pixels = np.sum(snow_mask & valid_pixels)
        snow_ratio = (snow_pixels / total_pixels) * 100  # 积雪覆盖率百分比

        results.append({'date': date_obj, 'snow_cover_percentage': snow_ratio})
        print(f"成功处理 {date_obj.strftime('%Y-%m-%d')}: 目标区域内积雪覆盖率 {snow_ratio:.2f}%")

    except Exception as e:
        print(f"处理 {folder} 时出错: {e}")
        traceback.print_exc()
        continue

# 检查结果
if not results:
    print("未成功处理任何数据，请检查路径和文件格式。")
    exit()

# 5. 数据处理和保存
df = pd.DataFrame(results)
df = df.groupby('date').mean().reset_index()
df.sort_values('date', inplace=True)
df.set_index('date', inplace=True)

# 计算雪深值（米）
def calculate_snow_depth(percentage):
    """
    将积雪覆盖率转换为雪深值（米）
    - 当覆盖率 ≤ 0% 时，雪深为 0 米
    - 当覆盖率 ≥ 100% 时，雪深为最大值
    - 其他情况按非线性映射
    """
    if percentage <= 0:
        return 0.0
    elif percentage >= 100:
        return SNOW_DEPTH_MAX
    else:
        return ((percentage / 100) / (1 - (percentage / 100))) ** (1/4) * SNOW_DEPTH_MAX / 2

# 添加雪深列
df['snow_depth_m'] = df['snow_cover_percentage'].apply(calculate_snow_depth)

print("\n处理结果预览:")
print(df.head())

# 保存结果到CSV文件 - 使用用户定义的文件名
csv_fullname = f"{CSV_FILENAME}.csv"
df.to_csv(csv_fullname)
print(f"结果已保存到 {csv_fullname}")

# 6. 绘图
try:
    plt.figure(figsize=(14, 7))
    
    # 绘制雪深折线图
    plt.plot(df.index, df['snow_depth_m'], marker='o', linestyle='-', linewidth=2, markersize=6)
    
    # 使用用户定义的标题
    plt.title(PLOT_TITLE, fontsize=16)
    
    plt.xlabel('日期', fontsize=14)
    plt.ylabel(f'雪深 (米)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 添加数据标签
    for i, row in df.iterrows():
        plt.annotate(f"{row['snow_depth_m']:.1f}米", 
                    (i, row['snow_depth_m']), 
                    textcoords="offset points", 
                    xytext=(0,10), 
                    ha='center',
                    fontsize=8)
    
    # 设置Y轴范围
    plt.ylim(0, SNOW_DEPTH_MAX * 1.1)  # 0到最大值的1.1倍，留出一点空间
    
    # 优化日期显示格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    
    # 保存图表 - 使用用户定义的文件名
    plot_fullname = f"{PLOT_FILENAME}.png"
    plt.savefig(plot_fullname, dpi=300)
    print(f"图表已保存为 {plot_fullname}")
    
    # 尝试显示图表
    try:
        plt.show()
    except Exception as e:
        print(f"显示图表时出错: {e}")
        # 尝试在默认查看器中打开图像
        import os
        import subprocess
        try:
            if os.name == 'nt':  # Windows
                os.startfile(plot_fullname)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', plot_fullname])
            print("已在默认图像查看器中打开图表")
        except Exception as e:
            print(f"无法打开图像文件: {e}")
    
except Exception as e:
    print(f"绘制图表时出错: {e}")
    traceback.print_exc()

# 7. 打印最终结果
print("\n处理完成!")
print(f"成功处理 {len(results)}/{total} 个影像")
print(f"时间范围: {df.index.min().strftime('%Y-%m-%d')} 到 {df.index.max().strftime('%Y-%m-%d')}")
print(f"目标区域: {TARGET_BOUNDS}")
print(f"区域描述: {AREA_DESCRIPTION}")
print(f"雪深最大值: {SNOW_DEPTH_MAX}米")
print(f"平均积雪覆盖率: {df['snow_cover_percentage'].mean():.2f}%")
print(f"最大积雪覆盖率: {df['snow_cover_percentage'].max():.2f}% (日期: {df['snow_cover_percentage'].idxmax().strftime('%Y-%m-%d')})")
print(f"最小积雪覆盖率: {df['snow_cover_percentage'].min():.2f}% (日期: {df['snow_cover_percentage'].idxmin().strftime('%Y-%m-%d')})")

# 雪深统计信息
print(f"平均雪深: {df['snow_depth_m'].mean():.2f}米")
print(f"最大雪深: {df['snow_depth_m'].max():.2f}米 (日期: {df['snow_depth_m'].idxmax().strftime('%Y-%m-%d')})")
print(f"最小雪深: {df['snow_depth_m'].min():.2f}米 (日期: {df['snow_depth_m'].idxmin().strftime('%Y-%m-%d')})")

# 等待用户确认
input("按Enter键退出程序...")