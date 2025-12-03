import os
import pandas as pd
from tkinter import Tk, filedialog
import warnings
warnings.filterwarnings('ignore')

def select_folder():
    """选择包含CSV文件的文件夹"""
    root = Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory(title="选择包含CSV文件的文件夹")
    root.destroy()
    return folder_path

def merge_csv_to_excel():
    # 选择文件夹
    folder_path = select_folder()
    if not folder_path:
        print("未选择文件夹，程序退出")
        return
    
    # 获取所有CSV文件
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if not csv_files:
        print("文件夹中没有找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    # 创建一个空的DataFrame，用于存储最终结果
    result_df = pd.DataFrame()
    
    # 处理第一个文件，获取日期列
    first_file = csv_files[0]
    first_file_path = os.path.join(folder_path, first_file)
    first_data = pd.read_csv(first_file_path, usecols=['date', 'snow_depth_m'])
    
    # 将日期列添加到结果DataFrame
    result_df['date'] = first_data['date']
    
    # 处理所有文件
    for i, csv_file in enumerate(csv_files):
        try:
            file_path = os.path.join(folder_path, csv_file)
            # 读取CSV文件，只获取snow_depth_m列
            df = pd.read_csv(file_path, usecols=['snow_depth_m'])
            
            # 获取文件名（不含扩展名）作为列名
            col_name = os.path.splitext(csv_file)[0]
            
            # 将snow_depth_m数据添加到结果DataFrame
            result_df[col_name] = df['snow_depth_m']
            
            print(f"已处理 {i+1}/{len(csv_files)}: {csv_file}")
            
        except Exception as e:
            print(f"处理文件 {csv_file} 时出错: {str(e)}")
            continue
    
    if result_df.empty:
        print("没有成功提取任何数据")
        return
    
    # 选择保存Excel文件的位置
    root = Tk()
    root.withdraw()
    output_path = filedialog.asksaveasfilename(
        title="保存Excel文件",
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )
    root.destroy()
    
    if not output_path:
        print("未选择保存位置，程序退出")
        return
    
    # 保存到Excel文件
    try:
        result_df.to_excel(output_path, index=False)
        print(f"数据已成功保存到: {output_path}")
        print(f"合并了 {len(result_df)} 行数据和 {len(csv_files)} 个文件的数据")
    except Exception as e:
        print(f"保存Excel文件时出错: {str(e)}")

if __name__ == "__main__":
    merge_csv_to_excel()