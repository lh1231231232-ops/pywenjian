import os
import json
import requests
from datetime import datetime, timedelta
import time
from pathlib import Path
from urllib.parse import urljoin
import threading
from queue import Queue
import geopandas as gpd
from shapely.geometry import Polygon, mapping
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== 配置区域 ====================
# 在这里直接设置您的哥白尼数据空间账户信息
USERNAME = "your_username_here"  # 替换为您的用户名
PASSWORD = "your_password_here"  # 替换为您的密码

# 设置默认下载目录
DEFAULT_DOWNLOAD_DIR = r"C:\Sentinel2_Downloads"  # 替换为您想要的默认路径

# 设置默认搜索参数
DEFAULT_START_DATE = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')  # 默认开始日期：30天前
DEFAULT_END_DATE = datetime.now().strftime('%Y-%m-%d')  # 默认结束日期：今天
DEFAULT_CLOUD_COVER = 30  # 默认最大云量30%
DEFAULT_PRODUCT_TYPE = "S2MSI2A"  # 默认产品类型: Level-2A
# ================================================

class CopernicusDataSpaceDownloader:
    def __init__(self):
        self.base_url = "https://catalogue.dataspace.copernicus.eu/resto"
        self.auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        self.download_url = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"
        self.session = requests.Session()
        self.access_token = None
        self.token_expiry = None
        
    def authenticate(self, username, password):
        """认证并获取访问令牌"""
        print("正在进行身份验证...")
        
        auth_data = {
            'client_id': 'cdse-public',
            'username': username,
            'password': password,
            'grant_type': 'password'
        }
        
        try:
            # 添加更详细的请求头
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.post(
                self.auth_url, 
                data=auth_data, 
                headers=headers,
                verify=False
            )
            
            # 打印响应状态和内容（用于调试）
            print(f"认证响应状态: {response.status_code}")
            if response.status_code != 200:
                print(f"认证响应内容: {response.text}")
            
            response.raise_for_status()
            
            auth_info = response.json()
            self.access_token = auth_info['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=auth_info['expires_in'] - 60)  # 提前60秒过期
            
            # 更新会话头
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            print("身份验证成功!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"身份验证失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text}")
            return False
    
    def check_token_validity(self):
        """检查令牌是否有效，必要时刷新"""
        if not self.access_token or datetime.now() >= self.token_expiry:
            print("访问令牌已过期，需要重新认证")
            return False
        return True
    
    def search_products(self, geometry, start_date, end_date, cloud_cover=30, product_type="S2MSI2A"):
        """搜索符合条件的哨兵二号产品"""
        print("正在搜索产品...")
        
        search_url = f"{self.base_url}/api/collections/Sentinel2/search.json"
        
        params = {
            'maxRecords': 100,  # 最大记录数
            'startDate': start_date,
            'completionDate': end_date,
            'cloudCover': f"[0,{cloud_cover}]",
            'productType': product_type,
            'geometry': geometry
        }
        
        try:
            response = self.session.get(search_url, params=params, verify=False)
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            print(f"找到 {len(features)} 个匹配的产品")
            return features
            
        except requests.exceptions.RequestException as e:
            print(f"搜索产品时出错: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            return []
    
    def get_download_info(self, product_id):
        """获取产品的下载信息"""
        print(f"获取产品 {product_id} 的下载信息...")
        
        # 使用新的API端点获取下载信息
        info_url = f"{self.download_url}({product_id})"
        
        try:
            response = self.session.get(info_url, verify=False)
            response.raise_for_status()
            
            product_info = response.json()
            return product_info
            
        except requests.exceptions.RequestException as e:
            print(f"获取产品信息时出错: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            return None
    
    def download_product(self, product_id, output_path):
        """下载单个产品"""
        try:
            # 使用新的下载端点
            download_endpoint = f"{self.download_url}({product_id})/$value"
            
            # 创建分块下载
            with self.session.get(download_endpoint, stream=True, verify=False) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 显示进度
                            if total_size > 0:
                                percent = (downloaded_size / total_size) * 100
                                print(f"\r下载进度: {percent:.1f}% ({downloaded_size}/{total_size} bytes)", end='')
                
                print(f"\n下载完成: {output_path}")
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"下载产品时出错: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            return False

def get_download_directory():
    """获取下载目录"""
    print("\n=== 设置下载目录 ===")
    
    # 使用默认下载目录
    download_dir = DEFAULT_DOWNLOAD_DIR
    
    # 检查目录是否存在，如果不存在则创建
    if not os.path.exists(download_dir):
        print(f"目录 '{download_dir}' 不存在，正在创建...")
        os.makedirs(download_dir, exist_ok=True)
        print(f"已创建目录: {download_dir}")
    
    return download_dir

def get_search_parameters():
    """获取搜索参数"""
    print("\n=== 设置搜索参数 ===")
    
    # 选择时间范围设置方式
    print("请选择时间范围设置方式:")
    print("1. 使用默认时间范围 (过去30天)")
    print("2. 手动输入开始和结束日期")
    
    choice = input("请选择 (1 或 2, 默认: 1): ") or "1"
    
    if choice == "1":
        # 使用默认时间范围
        start_date = DEFAULT_START_DATE
        end_date = DEFAULT_END_DATE
        print(f"使用默认时间范围: {start_date} 到 {end_date}")
    else:
        # 手动输入日期
        while True:
            try:
                start_date_input = input("请输入开始日期 (格式: YYYY-MM-DD, 例如: 2023-01-01): ")
                end_date_input = input("请输入结束日期 (格式: YYYY-MM-DD, 例如: 2023-01-31): ")
                
                # 验证日期格式
                datetime.strptime(start_date_input, '%Y-%m-%d')
                datetime.strptime(end_date_input, '%Y-%m-%d')
                
                # 确保开始日期不晚于结束日期
                if start_date_input > end_date_input:
                    print("错误: 开始日期不能晚于结束日期，请重新输入。")
                    continue
                
                start_date = start_date_input
                end_date = end_date_input
                break
                
            except ValueError:
                print("日期格式错误，请使用 YYYY-MM-DD 格式，例如: 2023-01-01")
    
    # 获取云量覆盖限制
    cloud_cover_input = input(f"最大云量覆盖百分比 (0-100, 默认: {DEFAULT_CLOUD_COVER}): ")
    max_cloud_cover = int(cloud_cover_input) if cloud_cover_input else DEFAULT_CLOUD_COVER
    
    # 获取产品类型
    product_type_input = input(f"产品类型 (S2MSI1C=Level-1C, S2MSI2A=Level-2A, 默认: {DEFAULT_PRODUCT_TYPE}): ")
    product_type = product_type_input if product_type_input else DEFAULT_PRODUCT_TYPE
    
    return start_date, end_date, max_cloud_cover, product_type

def read_shapefile(shapefile_path):
    """读取Shapefile文件并提取几何信息"""
    try:
        # 读取Shapefile
        gdf = gpd.read_file(shapefile_path)
        
        # 检查坐标系，如果需要则转换为WGS84
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            print(f"检测到非WGS84坐标系 (EPSG:{gdf.crs.to_epsg()})，正在转换为WGS84...")
            gdf = gdf.to_crs(epsg=4326)
        
        # 合并所有几何图形
        union_geometry = gdf.unary_union
        
        # 转换为GeoJSON格式
        if union_geometry.geom_type == 'Polygon':
            geojson_geometry = mapping(union_geometry)
        else:
            # 如果是多面或多边形集合，取第一个多边形
            if hasattr(union_geometry, 'geoms'):
                geojson_geometry = mapping(union_geometry.geoms[0])
            else:
                geojson_geometry = mapping(union_geometry)
        
        # 转换为WKT格式
        coords = geojson_geometry['coordinates'][0]
        wkt_coords = ", ".join([f"{coord[0]} {coord[1]}" for coord in coords])
        wkt_geometry = f"POLYGON(({wkt_coords}))"
        
        return wkt_geometry
        
    except Exception as e:
        print(f"读取Shapefile文件时出错: {e}")
        return None

def get_search_area():
    """获取搜索区域"""
    print("\n=== 设置搜索区域 ===")
    print("请选择区域定义方式:")
    print("1. 使用GeoJSON文件")
    print("2. 使用Shapefile文件")
    print("3. 手动输入边界坐标")
    
    choice = input("请选择 (1, 2 或 3, 默认: 1): ") or "1"
    
    if choice == "1":
        geojson_path = input("请输入GeoJSON文件路径: ")
        try:
            with open(geojson_path, 'r') as f:
                geojson_data = json.load(f)
            
            # 提取坐标并创建WKT格式
            coordinates = geojson_data['features'][0]['geometry']['coordinates'][0]
            wkt_coords = ", ".join([f"{coord[0]} {coord[1]}" for coord in coordinates])
            geometry = f"POLYGON(({wkt_coords}))"
            
            return geometry
        except Exception as e:
            print(f"读取GeoJSON文件时出错: {e}")
            return get_search_area_manual()
    
    elif choice == "2":
        shapefile_path = input("请输入Shapefile文件路径 (.shp): ")
        geometry = read_shapefile(shapefile_path)
        if geometry:
            return geometry
        else:
            print("无法从Shapefile提取几何信息，请尝试其他方式。")
            return get_search_area_manual()
    
    else:
        return get_search_area_manual()

def get_search_area_manual():
    """手动输入边界坐标"""
    print("请输入区域的边界坐标 (格式: 最小经度,最小纬度,最大经度,最大纬度)")
    print("例如: 13.0,45.0,13.5,45.5")
    
    while True:
        try:
            coords = input("坐标: ").split(',')
            if len(coords) != 4:
                raise ValueError("需要4个坐标值")
            
            min_lon, min_lat, max_lon, max_lat = map(float, coords)
            geometry = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
            return geometry
        except ValueError as e:
            print(f"输入错误: {e}，请重新输入")

def main():
    """主函数"""
    # 使用预设的用户名和密码
    username, password = USERNAME, PASSWORD
    
    # 获取下载目录
    download_dir = get_download_directory()
    
    # 获取搜索区域
    geometry = get_search_area()
    
    # 获取搜索参数
    start_date, end_date, max_cloud_cover, product_type = get_search_parameters()
    
    # 初始化下载器
    downloader = CopernicusDataSpaceDownloader()
    
    # 认证
    if not downloader.authenticate(username, password):
        print("认证失败，请检查您的用户名和密码是否正确")
        print("请注意：哥白尼数据空间需要单独注册账户，与SciHub账户不同")
        print("注册地址：https://dataspace.copernicus.eu/")
        return
    
    # 搜索产品
    products = downloader.search_products(geometry, start_date, end_date, max_cloud_cover, product_type)
    
    if not products:
        print("未找到匹配的产品。")
        return
    
    # 显示找到的产品
    print("\n找到的产品列表:")
    for i, product in enumerate(products):
        props = product.get('properties', {})
        title = props.get('title', '未知')
        product_id = product.get('id', '未知')  # 使用UUID而不是productIdentifier
        cloud_cover = props.get('cloudCover', '未知')
        acquisition_date = props.get('startDate', '未知').split('T')[0]  # 提取日期部分
        print(f"{i+1}. {title} (日期: {acquisition_date}, 云量: {cloud_cover}%)")
    
    # 选择要下载的产品
    selection = input("\n请输入要下载的产品编号(多个产品用逗号分隔，或输入'all'下载所有): ")
    
    if selection.lower() == 'all':
        selected_products = products
    else:
        try:
            indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
            selected_products = [products[i] for i in indices if 0 <= i < len(products)]
        except ValueError:
            print("输入格式错误，请重新运行程序。")
            return
    
    print(f"\n准备下载 {len(selected_products)} 个产品...")
    
    # 下载选中的产品
    for i, product in enumerate(selected_products):
        props = product.get('properties', {})
        product_id = product.get('id')  # 使用UUID而不是productIdentifier
        title = props.get('title', '未知产品')
        
        print(f"\n[{i+1}/{len(selected_products)}] 处理产品: {title}")
        
        # 检查令牌有效性
        if not downloader.check_token_validity():
            print("令牌已失效，尝试重新认证...")
            if not downloader.authenticate(username, password):
                print("重新认证失败，终止下载")
                return
        
        # 创建输出文件名
        output_filename = f"{title}.zip"
        output_path = os.path.join(download_dir, output_filename)
        
        # 检查文件是否已存在
        if os.path.exists(output_path):
            overwrite = input(f"文件 {output_filename} 已存在，是否覆盖? (y/n): ").lower()
            if overwrite != 'y':
                print("跳过下载")
                continue
        
        # 直接下载产品，不再尝试获取下载链接
        print(f"开始下载: {output_filename}")
        success = downloader.download_product(product_id, output_path)
        
        if success:
            print(f"成功下载: {output_filename}")
        else:
            print(f"下载失败: {output_filename}")
        
        # 添加短暂延迟，避免请求过于频繁
        time.sleep(1)
    
    print("\n所有下载任务已完成!")

if __name__ == "__main__":
    # 检查必要的依赖
    try:
        import geopandas
        print("geopandas 已安装，支持Shapefile文件")
    except ImportError:
        print("警告: geopandas 未安装，Shapefile支持受限")
        print("要安装geopandas，请运行: pip install geopandas")
    
    main()