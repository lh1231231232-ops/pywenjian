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
import warnings
warnings.filterwarnings('ignore')

# 设置matplotlib后端以避免PyCharm兼容性问题
matplotlib.use('TkAgg')  # 使用Tkinter作为后端

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']

# 1. 设置路径
base_path = r"E:\yx"

# 2. 获取Excel文件中的最大雪深值
def get_snow_depth_from_excel():
    print("\n请提供包含最大雪深值的Excel文件路径")
    while True:
        excel_path = input("请输入Excel文件完整路径: ").strip()
        
        if not os.path.exists(excel_path):
            print("错误：文件不存在，请重新输入")
            continue
        
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_path)
            
            # 检查列名
            if len(df.columns) < 2:
                print("错误：Excel文件需要至少两列，第一列为区域名称，第二列为最大雪深值")
                continue
            
            # 假设第一列是区域名称，第二列是最大雪深值
            region_col = df.columns[0]
            depth_col = df.columns[1]
            
            # 创建区域名称到最大雪深值的映射
            snow_depth_map = {}
            for _, row in df.iterrows():
                region_name = row[region_col]
                snow_depth = row[depth_col]
                
                # 检查雪深值是否有效
                if pd.isna(snow_depth) or snow_depth <= 0:
                    print(f"警告: 区域 '{region_name}' 的最大雪深值无效，将使用默认值3.5米")
                    snow_depth = 3.5
                
                snow_depth_map[region_name] = snow_depth
            
            print(f"成功读取 {len(snow_depth_map)} 个区域的最大雪深值")
            return snow_depth_map, excel_path
            
        except Exception as e:
            print(f"读取Excel文件时出错: {e}")
            print("请检查文件格式是否正确")
            continue

# 3. 获取shp文件中的所有区域
def get_all_regions_from_shp():
    print("\n请提供shp文件路径")
    while True:
        shp_path = input("请输入shp文件完整路径: ").strip()
        
        if not os.path.exists(shp_path):
            print("错误：文件不存在，请重新输入")
            continue
        
        try:
            # 读取shp文件
            gdf = gpd.read_file(shp_path)
            
            # 检查O_Name字段是否存在
            if 'O_Name' not in gdf.columns:
                print("错误：shp文件中没有找到O_Name字段")
                print(f"可用字段: {list(gdf.columns)}")
                continue
            
            # 获取所有唯一的O_Name值
            regions = gdf['O_Name'].unique()
            print(f"\n找到 {len(regions)} 个区域:")
            for i, region in enumerate(regions):
                print(f"{i+1}. {region}")
            
            # 获取每个区域的几何形状和范围
            region_data = []
            for region in regions:
                region_gdf = gdf[gdf['O_Name'] == region]
                
                # 获取区域的总体范围
                total_bounds = region_gdf.total_bounds
                
                # 如果是地理坐标系，直接使用
                if region_gdf.crs and region_gdf.crs.is_geographic:
                    min_lon, min_lat, max_lon, max_lat = total_bounds
                else:
                    # 如果不是地理坐标系，转换为WGS84 (EPSG:4326)
                    region_gdf_wgs84 = region_gdf.to_crs(epsg=4326)
                    total_bounds = region_gdf_wgs84.total_bounds
                    min_lon, min_lat, max_lon, max_lat = total_bounds
                
                region_data.append({
                    'name': region,
                    'bounds': [min_lon, min_lat, max_lon, max_lat],
                    'geometry': region_gdf.geometry.iloc[0] if len(region_gdf) == 1 else region_gdf.unary_union
                })
            
            return region_data, shp_path
            
        except Exception as e:
            print(f"读取shp文件时出错: {e}")
            print("请检查文件格式是否正确")
            continue

# 获取输出目录
def get_output_directory():
    print("\n请设置输出文件的目录")
    print("注意：所有区域的CSV和PNG文件将保存在此目录中")
    
    while True:
        output_dir = input("请输入输出目录路径（或按Enter使用当前目录）: ").strip()
        
        if not output_dir:
            output_dir = os.getcwd()
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(f"创建目录: {output_dir}")
            except Exception as e:
                print(f"无法创建目录: {e}")
                continue
        
        return output_dir

# 获取Excel文件中的最大雪深值
snow_depth_map, excel_path = get_snow_depth_from_excel()
print(f"从Excel文件中读取了 {len(snow_depth_map)} 个区域的最大雪深值")

# 获取输出目录
OUTPUT_DIR = get_output_directory()
print(f"输出目录设置为: {OUTPUT_DIR}")

# 获取所有区域
regions, shp_path = get_all_regions_from_shp()

# 4. 自动发现所有可用的影像数据
safe_folders = glob.glob(os.path.join(base_path, "*.SAFE"))
print(f"发现 {len(safe_folders)} 个 Sentinel-2 数据集")

# 处理每个区域
for region in regions:
    region_name = region['name']
    region_bounds = region['bounds']
    
    # 获取该区域的最大雪深值
    if region_name in snow_depth_map:
        region_snow_depth_max = snow_depth_map[region_name]
    else:
        print(f"警告: 区域 '{region_name}' 在Excel文件中未找到，使用默认值3.5米")
        region_snow_depth_max = 3.5
    
    print(f"\n开始处理区域: {region_name}")
    print(f"区域范围: {region_bounds}")
    print(f"最大雪深值: {region_snow_depth_max}米")
    
    # 用于存储结果的列表
    results = []
    
    # 5. 遍历处理每一景影像
    total = len(safe_folders)
    processed = 0
    
    for folder in safe_folders:
        processed += 1
        try:
            print(f"\n处理影像 ({processed}/{total}): {os.path.basename(folder)}")
            print(f"内存使用: {psutil.virtual_memory().percent}%")
            
            # 5.1 从文件夹名称中提取日期
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

            # 5.2 查找波段文件
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

            # 5.3 打开波段并裁剪到目标区域
            try:
                with rasterio.open(band_b3_path) as src_b3:
                    # 将目标区域从WGS84转换到影像的CRS
                    if src_b3.crs != CRS.from_epsg(4326):
                        transformed_bounds = transform_bounds(
                            CRS.from_epsg(4326), 
                            src_b3.crs, 
                            region_bounds[0], region_bounds[1], 
                            region_bounds[2], region_bounds[3]
                        )
                    else:
                        transformed_bounds = region_bounds
                    
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
                            region_bounds[0], region_bounds[1], 
                            region_bounds[2], region_bounds[3]
                        )
                    else:
                        transformed_bounds_b11 = region_bounds
                    
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

            # 5.4 计算NDSI（归一化差分雪指数）
            np.seterr(divide='ignore', invalid='ignore')  # 忽略除以零的警告
            ndsi = (green - swir) / (green + swir)

            # 5.5 创建积雪掩膜 (NDSI > 0.4 通常被认为是雪)
            snow_mask = ndsi > 0.4

            # 5.6 计算积雪像素占总像素的比例
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
        print(f"区域 {region_name} 未成功处理任何数据，跳过")
        continue

    # 6. 数据处理和保存
    df = pd.DataFrame(results)
    df = df.groupby('date').mean().reset_index()
    df.sort_values('date', inplace=True)
    df.set_index('date', inplace=True)

    # 计算雪深值（米）
    def calculate_snow_depth(percentage, max_depth):
        """
        将积雪覆盖率转换为雪深值（米）
        - 当覆盖率 ≤ 0% 时，雪深为 0 米
        - 当覆盖率 ≥ 100% 时，雪深为最大值
        - 其他情况按非线性映射
        """
        if percentage <= 0:
            return 0.0
        elif percentage >= 100:
            return max_depth
        else:
            return ((percentage / 100) / (1 - (percentage / 100))) ** (1/4) * max_depth / 2

    # 添加雪深列，使用该区域的最大雪深值
    df['snow_depth_m'] = df['snow_cover_percentage'].apply(
        lambda x: calculate_snow_depth(x, region_snow_depth_max)
    )

    print(f"\n区域 {region_name} 处理结果预览:")
    print(df.head())

    # 清理文件名中的非法字符
    def clean_filename(name):
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name

    clean_region_name = clean_filename(region_name)
    
    # 保存结果到CSV文件 - 使用区域名称作为文件名
    csv_filename = f"{clean_region_name}.csv"
    csv_fullpath = os.path.join(OUTPUT_DIR, csv_filename)
    df.to_csv(csv_fullpath)
    print(f"结果已保存到 {csv_fullpath}")

    # 7. 绘图
    try:
        plt.figure(figsize=(14, 7))
        
        # 绘制雪深折线图
        plt.plot(df.index, df['snow_depth_m'], marker='o', linestyle='-', linewidth=2, markersize=6)
        
        # 使用区域名称和最大雪深值作为标题
        plt.title(f'Sentinel-2 积雪覆盖时间序列\n区域: {region_name} (最大雪深: {region_snow_depth_max}米)', fontsize=16)
        
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
        plt.ylim(0, region_snow_depth_max * 1.1)  # 0到最大值的1.1倍，留出一点空间
        
        # 优化日期显示格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        
        # 保存图表 - 使用区域名称作为文件名
        plot_filename = f"{clean_region_name}.png"
        plot_fullpath = os.path.join(OUTPUT_DIR, plot_filename)
        plt.savefig(plot_fullpath, dpi=300)
        print(f"图表已保存为 {plot_fullpath}")
        
        # 关闭图表以释放内存
        plt.close()
        
    except Exception as e:
        print(f"绘制图表时出错: {e}")
        traceback.print_exc()

    # 打印区域处理结果
    print(f"\n区域 {region_name} 处理完成!")
    print(f"成功处理 {len(results)}/{total} 个影像")
    print(f"时间范围: {df.index.min().strftime('%Y-%m-%d')} 到 {df.index.max().strftime('%Y-%m-%d')}")
    print(f"区域范围: {region_bounds}")
    print(f"最大雪深值: {region_snow_depth_max}米")
    print(f"平均积雪覆盖率: {df['snow_cover_percentage'].mean():.2f}%")
    print(f"最大积雪覆盖率: {df['snow_cover_percentage'].max():.2f}% (日期: {df['snow_cover_percentage'].idxmax().strftime('%Y-%m-%d')})")
    print(f"最小积雪覆盖率: {df['snow_cover_percentage'].min():.2f}% (日期: {df['snow_cover_percentage'].idxmin().strftime('%Y-%m-%d')})")
    
    # 雪深统计信息
    print(f"平均雪深: {df['snow_depth_m'].mean():.2f}米")
    print(f"最大雪深: {df['snow_depth_m'].max():.2f}米 (日期: {df['snow_depth_m'].idxmax().strftime('%Y-%m-%d')})")
    print(f"最小雪深: {df['snow_depth_m'].min():.2f}米 (日期: {df['snow_depth_m'].idxmin().strftime('%Y-%m-%d')})")

# 所有区域处理完成
print("\n所有区域处理完成!")
print(f"输出文件保存在: {OUTPUT_DIR}")

# 等待用户确认
input("按Enter键退出程序...")