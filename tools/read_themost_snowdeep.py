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
base_path = r"E:\合集\000000"

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


def parse_date_from_name(path_or_name):
    """从文件名中提取日期，支持 YYYYMMDD / YYYY_MM_DD / YYYY_MM 等格式。"""
    name = os.path.basename(path_or_name)

    # 1) 优先匹配完整日期
    match_full = re.search(r'(\d{4})[\.\-_]?(\d{2})[\.\-_]?(\d{2})', name)
    if match_full:
        year, month, day = match_full.groups()
        try:
            return datetime.strptime(f"{year}{month}{day}", "%Y%m%d")
        except ValueError:
            pass

    # 2) 匹配年月（例如 roi_monthly_2016_03_L8L9.tif）
    match_month = re.search(r'(\d{4})[\.\-_](\d{2})(?!\d)', name)
    if match_month:
        year, month = match_month.groups()
        try:
            return datetime.strptime(f"{year}{month}01", "%Y%m%d")
        except ValueError:
            pass

    # 3) Sentinel 常见命名兜底
    parts = name.split('_')
    if len(parts) >= 3:
        date_str = parts[2][:8]
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except (ValueError, IndexError):
            pass

    return None


def discover_image_sources(base_dir):
    """自动发现可处理的数据源：Sentinel SAFE + GeoTIFF。"""
    safe_folders = sorted(glob.glob(os.path.join(base_dir, "*.SAFE")))

    tif_files = glob.glob(os.path.join(base_dir, "**", "*.tif"), recursive=True)
    tiff_files = glob.glob(os.path.join(base_dir, "**", "*.tiff"), recursive=True)
    raster_files = sorted(set(tif_files + tiff_files))

    image_sources = []
    image_sources.extend([{'type': 'SAFE', 'path': p} for p in safe_folders])
    image_sources.extend([{'type': 'RASTER', 'path': p} for p in raster_files])

    return image_sources, safe_folders, raster_files


def find_band_by_metadata(src, candidates):
    """根据波段描述/标签关键字查找波段索引（1-based）。"""
    candidates_upper = [c.upper() for c in candidates]

    for idx in range(1, src.count + 1):
        desc = (src.descriptions[idx - 1] or '').upper() if src.descriptions else ''
        tags_text = ' '.join(str(v).upper() for v in src.tags(idx).values())
        searchable = f"{desc} {tags_text}"

        if any(c in searchable for c in candidates_upper):
            return idx

    return None


def read_single_band_by_bounds(src, region_bounds, band_index):
    """按区域范围裁剪并读取单波段。"""
    if src.crs and src.crs != CRS.from_epsg(4326):
        transformed_bounds = transform_bounds(
            CRS.from_epsg(4326),
            src.crs,
            region_bounds[0], region_bounds[1],
            region_bounds[2], region_bounds[3]
        )
    else:
        transformed_bounds = region_bounds

    try:
        window = from_bounds(
            transformed_bounds[0], transformed_bounds[1],
            transformed_bounds[2], transformed_bounds[3],
            transform=src.transform
        )
        window = window.intersection((0, 0, src.height, src.width))

        if window.height == 0 or window.width == 0:
            raise ValueError("目标区域在影像范围之外")

        data = src.read(band_index, window=window).astype(np.float32)
        transform_cropped = src.window_transform(window)
        return data, transform_cropped

    except Exception:
        row_min, col_min = src.index(transformed_bounds[0], transformed_bounds[3])
        row_max, col_max = src.index(transformed_bounds[2], transformed_bounds[1])

        row_min = max(0, row_min)
        row_max = min(src.height, row_max)
        col_min = max(0, col_min)
        col_max = min(src.width, col_max)

        if row_min >= row_max or col_min >= col_max:
            raise ValueError("目标区域在影像范围之外")

        window = ((row_min, row_max), (col_min, col_max))
        data = src.read(band_index, window=window).astype(np.float32)
        transform_cropped = src.window_transform(window)
        return data, transform_cropped


def read_multi_band_by_bounds(src, region_bounds, band_indexes):
    """按区域范围裁剪并读取多个波段。"""
    if src.crs and src.crs != CRS.from_epsg(4326):
        transformed_bounds = transform_bounds(
            CRS.from_epsg(4326),
            src.crs,
            region_bounds[0], region_bounds[1],
            region_bounds[2], region_bounds[3]
        )
    else:
        transformed_bounds = region_bounds

    try:
        window = from_bounds(
            transformed_bounds[0], transformed_bounds[1],
            transformed_bounds[2], transformed_bounds[3],
            transform=src.transform
        )
        window = window.intersection((0, 0, src.height, src.width))

        if window.height == 0 or window.width == 0:
            raise ValueError("目标区域在影像范围之外")

        data = src.read(band_indexes, window=window).astype(np.float32)
        transform_cropped = src.window_transform(window)
        return data, transform_cropped

    except Exception:
        row_min, col_min = src.index(transformed_bounds[0], transformed_bounds[3])
        row_max, col_max = src.index(transformed_bounds[2], transformed_bounds[1])

        row_min = max(0, row_min)
        row_max = min(src.height, row_max)
        col_min = max(0, col_min)
        col_max = min(src.width, col_max)

        if row_min >= row_max or col_min >= col_max:
            raise ValueError("目标区域在影像范围之外")

        window = ((row_min, row_max), (col_min, col_max))
        data = src.read(band_indexes, window=window).astype(np.float32)
        transform_cropped = src.window_transform(window)
        return data, transform_cropped


def snow_mask_from_rgb(rgb_data):
    """彩色影像兜底：基于亮度 + 低饱和度估计雪像元。"""
    red = rgb_data[0]
    green = rgb_data[1]
    blue = rgb_data[2]

    valid_pixels = np.isfinite(red) & np.isfinite(green) & np.isfinite(blue)
    if np.sum(valid_pixels) == 0:
        return np.zeros_like(red, dtype=bool), valid_pixels

    brightness = (red + green + blue) / 3.0
    max_rgb = np.maximum(np.maximum(red, green), blue)
    min_rgb = np.minimum(np.minimum(red, green), blue)
    saturation = (max_rgb - min_rgb) / (max_rgb + 1e-6)

    bright_threshold = np.nanpercentile(brightness[valid_pixels], 70)
    snow_mask = (
        valid_pixels
        & (brightness >= bright_threshold)
        & (saturation <= 0.25)
        & (green >= red * 0.9)
        & (green >= blue * 0.9)
    )
    return snow_mask, valid_pixels

# 获取Excel文件中的最大雪深值
snow_depth_map, excel_path = get_snow_depth_from_excel()
print(f"从Excel文件中读取了 {len(snow_depth_map)} 个区域的最大雪深值")

# 获取输出目录
OUTPUT_DIR = get_output_directory()
print(f"输出目录设置为: {OUTPUT_DIR}")

# 获取所有区域
regions, shp_path = get_all_regions_from_shp()

# 4. 自动发现所有可用的影像数据
image_sources, safe_folders, raster_files = discover_image_sources(base_path)
print(f"发现 {len(safe_folders)} 个 Sentinel-2 SAFE 数据集")
print(f"发现 {len(raster_files)} 个 GeoTIFF 影像")
print(f"总计可处理数据源: {len(image_sources)}")

if not image_sources:
    print("警告: 未发现任何可处理影像，请检查 base_path")

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
    total = len(image_sources)
    processed = 0
    
    for source in image_sources:
        processed += 1
        try:
            source_path = source['path']
            source_type = source['type']
            source_name = os.path.basename(source_path)

            print(f"\n处理影像 ({processed}/{total}): {source_name} [{source_type}]")
            print(f"内存使用: {psutil.virtual_memory().percent}%")
            
            # 5.1 从文件夹名称中提取日期
            date_obj = parse_date_from_name(source_name)
            if date_obj is None:
                print(f"警告: 无法从名称 {source_name} 中提取日期，使用默认日期")
                date_obj = datetime.now()
            
            print(f"处理日期: {date_obj.strftime('%Y-%m-%d')}")

            if source_type == 'SAFE':
                folder = source_path

                # 5.2 查找波段文件
                band_b3_path = None
                band_b11_path = None

                b3_patterns = [
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R10m', '*_B03_10m.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*_B03_20m.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B03_*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*_B03_*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R10m', '*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'T*_B03.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B03.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*B03*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*', '*B03*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*', '*B03.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*B03.jp2')
                ]

                b11_patterns = [
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*_B11_20m.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B11_*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*_B11_*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R20m', '*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'T*_B11.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_B11.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*B11*.jp2'),
                    os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*', '*B11*.jp2')
                ]

                for pattern in b3_patterns:
                    band_b3_list = glob.glob(pattern)
                    if band_b3_list:
                        band_b3_path = band_b3_list[0]
                        break

                for pattern in b11_patterns:
                    band_b11_list = glob.glob(pattern)
                    if band_b11_list:
                        band_b11_path = band_b11_list[0]
                        break

                if not band_b3_path:
                    print(f"错误: 在 {folder} 中未找到绿光波段 (B03) 文件，跳过")
                    continue

                if not band_b11_path:
                    print(f"错误: 在 {folder} 中未找到短波红外波段 (B11) 文件，跳过")
                    continue

                print(f"使用绿光波段: {band_b3_path}")
                print(f"使用短波红外波段: {band_b11_path}")

                try:
                    with rasterio.open(band_b3_path) as src_b3:
                        green, transform_cropped = read_single_band_by_bounds(src_b3, region_bounds, 1)
                        profile = src_b3.profile
                except Exception as e:
                    print(f"打开绿光波段失败: {e}")
                    continue

                try:
                    with rasterio.open(band_b11_path) as src_b11:
                        swir, transform_b11_cropped = read_single_band_by_bounds(src_b11, region_bounds, 1)

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

                np.seterr(divide='ignore', invalid='ignore')
                ndsi = (green - swir) / (green + swir)
                snow_mask = ndsi > 0.4
                valid_pixels = ~np.isnan(ndsi)

            else:
                # RASTER: 支持新的 GeoTIFF 输入
                try:
                    with rasterio.open(source_path) as src:
                        print(f"GeoTIFF波段数: {src.count}")

                        green_idx = find_band_by_metadata(src, ['B03', 'B3', 'GREEN'])
                        swir_idx = find_band_by_metadata(src, ['B11', 'SWIR1', 'SWIR', 'B06', 'B6'])

                        # 常见波段顺序兜底：Sentinel(3,11) / Landsat(3,6)
                        if src.count >= 11:
                            green_idx = green_idx or 3
                            swir_idx = swir_idx or 11
                        elif src.count >= 6:
                            green_idx = green_idx or 3
                            swir_idx = swir_idx or 6

                        if green_idx and swir_idx:
                            print(f"使用GeoTIFF波段: Green={green_idx}, SWIR={swir_idx}")
                            green, _ = read_single_band_by_bounds(src, region_bounds, green_idx)
                            swir, _ = read_single_band_by_bounds(src, region_bounds, swir_idx)

                            np.seterr(divide='ignore', invalid='ignore')
                            ndsi = (green - swir) / (green + swir)
                            snow_mask = ndsi > 0.4
                            valid_pixels = ~np.isnan(ndsi)

                        elif src.count >= 3:
                            print("提示: 未找到SWIR波段，当前按彩色影像模式识别积雪")
                            rgb, _ = read_multi_band_by_bounds(src, region_bounds, [1, 2, 3])
                            snow_mask, valid_pixels = snow_mask_from_rgb(rgb)

                        else:
                            print("错误: GeoTIFF波段不足（<3），无法识别积雪，跳过")
                            continue

                except Exception as e:
                    print(f"处理GeoTIFF失败: {e}")
                    continue

            total_pixels = np.sum(valid_pixels)
            
            if total_pixels == 0:
                print(f"警告: 没有有效像素，跳过")
                continue
                
            snow_pixels = np.sum(snow_mask & valid_pixels)
            snow_ratio = (snow_pixels / total_pixels) * 100  # 积雪覆盖率百分比

            results.append({'date': date_obj, 'snow_cover_percentage': snow_ratio})
            print(f"成功处理 {date_obj.strftime('%Y-%m-%d')}: 目标区域内积雪覆盖率 {snow_ratio:.2f}%")

        except Exception as e:
            print(f"处理 {source_path} 时出错: {e}")
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