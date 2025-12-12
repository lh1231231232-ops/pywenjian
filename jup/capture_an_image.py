import os
import glob
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import re
import geopandas as gpd
from rasterio.mask import mask
from rasterio.plot import show
from pyproj import CRS
import warnings
warnings.filterwarnings('ignore')

# 设置matplotlib后端
import matplotlib
matplotlib.use('TkAgg')

# 1. 获取用户输入
def get_user_input():
    print("请提供必要的文件路径")
    
    # 获取shp文件路径
    while True:
        shp_path = input("请输入shp文件完整路径: ").strip()
        if os.path.exists(shp_path):
            break
        print("错误：文件不存在，请重新输入")
    
    # 获取影像数据目录
    while True:
        image_dir = input("请输入Sentinel-2影像数据目录路径: ").strip()
        if os.path.exists(image_dir):
            break
        print("错误：目录不存在，请重新输入")
    
    # 获取输出目录
    output_dir = input("请输入输出目录路径（或按Enter使用当前目录）: ").strip()
    if not output_dir:
        output_dir = os.getcwd()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建目录: {output_dir}")
    
    return shp_path, image_dir, output_dir

# 2. 读取shp文件并获取所有区域
def get_regions_from_shp(shp_path):
    print("读取shp文件...")
    gdf = gpd.read_file(shp_path)
    
    # 检查O_Name字段是否存在
    if 'O_Name' not in gdf.columns:
        print("错误：shp文件中没有找到O_Name字段")
        print(f"可用字段: {list(gdf.columns)}")
        return None
    
    # 获取所有唯一的O_Name值
    regions = gdf['O_Name'].unique()
    print(f"找到 {len(regions)} 个区域")
    
    # 为每个区域创建几何信息
    region_data = []
    for region_name in regions:
        region_gdf = gdf[gdf['O_Name'] == region_name]
        
        # 合并同一区域的所有几何图形
        if len(region_gdf) > 1:
            union_geom = region_gdf.unary_union
        else:
            union_geom = region_gdf.geometry.iloc[0]
        
        region_data.append({
            'name': str(region_name),
            'geometry': union_geom,
            'crs': region_gdf.crs
        })
    
    return region_data

# 3. 查找TCIjp2文件
def find_tci_files(image_dir):
    print("查找TCIjp2文件...")
    safe_folders = glob.glob(os.path.join(image_dir, "*.SAFE"))
    tci_files = []
    
    for folder in safe_folders:
        # 可能的TCI文件路径模式
        tci_patterns = [
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R10m', '*_TCI_10m.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*_TCI*.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', 'R10m', '*.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*TCI*.jp2'),
            os.path.join(folder, 'GRANULE', '*', 'IMG_DATA', '*', '*TCI*.jp2')
        ]
        
        for pattern in tci_patterns:
            files = glob.glob(pattern)
            if files:
                tci_path = files[0]
                
                # 从文件夹名称中提取日期
                folder_name = os.path.basename(folder)
                date_match = re.search(r'(\d{4})(\d{2})(\d{2})', folder_name)
                if date_match:
                    year, month, day = date_match.groups()
                    date_str = f"{year}-{month}-{day}"
                else:
                    # 尝试从标准Sentinel-2命名格式中提取日期
                    parts = folder_name.split('_')
                    if len(parts) >= 3:
                        date_str = parts[2][:8]  # 例如 '20230101T100101' -> '20230101'
                        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    else:
                        date_str = "unknown_date"
                
                tci_files.append({
                    'path': tci_path,
                    'date': date_str,
                    'folder': folder_name
                })
                print(f"找到TCI文件: {tci_path} (日期: {date_str})")
                break
    
    return tci_files

# 4. 裁剪并保存影像
def crop_and_save_images(regions, tci_files, output_dir):
    print("开始裁剪影像...")
    
    for tci_file in tci_files:
        tci_path = tci_file['path']
        date_str = tci_file['date']
        
        print(f"\n处理影像: {os.path.basename(tci_path)} (日期: {date_str})")
        
        try:
            # 打开TCI文件
            with rasterio.open(tci_path) as src:
                print(f"影像CRS: {src.crs}")
                print(f"影像范围: {src.bounds}")
                
                # 对每个区域进行裁剪
                for region in regions:
                    region_name = region['name']
                    region_geom = region['geometry']
                    region_crs = region['crs']
                    
                    print(f"处理区域: {region_name}")
                    
                    # 如果区域CRS与影像CRS不同，需要转换几何图形
                    if region_crs != src.crs:
                        try:
                            # 转换几何图形到影像CRS
                            region_geom_transformed = gpd.GeoSeries([region_geom], crs=region_crs).to_crs(src.crs).iloc[0]
                        except Exception as e:
                            print(f"转换几何图形CRS时出错: {e}")
                            continue
                    else:
                        region_geom_transformed = region_geom
                    
                    try:
                        # 使用几何图形裁剪影像
                        out_image, out_transform = mask(src, [region_geom_transformed], crop=True, all_touched=True)
                        
                        # 检查裁剪后的图像是否为空
                        if out_image.size == 0:
                            print(f"区域 {region_name} 在影像中无数据，跳过")
                            continue
                        
                        # 创建输出元数据
                        out_meta = src.meta.copy()
                        out_meta.update({
                            "driver": "PNG",
                            "height": out_image.shape[1],
                            "width": out_image.shape[2],
                            "transform": out_transform,
                            "count": 3  # RGB三个波段
                        })
                        
                        # 清理文件名中的非法字符
                        def clean_filename(name):
                            invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
                            for char in invalid_chars:
                                name = name.replace(char, '_')
                            return name
                        
                        clean_region_name = clean_filename(region_name)
                        
                        # 创建输出文件名
                        output_filename = f"{clean_region_name}_{date_str}.png"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        # 保存为PNG
                        with rasterio.open(output_path, "w", **out_meta) as dest:
                            dest.write(out_image)
                        
                        print(f"已保存: {output_filename}")
                        
                    except Exception as e:
                        print(f"裁剪区域 {region_name} 时出错: {e}")
                        continue
                        
        except Exception as e:
            print(f"打开或处理TCI文件时出错: {e}")
            continue

# 主函数
def main():
    print("=== Sentinel-2影像区域裁剪工具 ===")
    
    # 获取用户输入
    shp_path, image_dir, output_dir = get_user_input()
    
    # 读取shp文件中的区域
    regions = get_regions_from_shp(shp_path)
    if not regions:
        return
    
    # 查找TCI文件
    tci_files = find_tci_files(image_dir)
    if not tci_files:
        print("未找到任何TCI文件")
        return
    
    # 裁剪并保存影像
    crop_and_save_images(regions, tci_files, output_dir)
    
    print("\n处理完成!")
    print(f"输出文件保存在: {output_dir}")

if __name__ == "__main__":
    main()
    input("按Enter键退出程序...")
