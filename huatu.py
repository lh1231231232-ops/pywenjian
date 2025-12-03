import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
from datetime import datetime

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# 创建保存图表的文件夹
save_dir = "chartss"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 您提供的Excel数据
# data = {
#     'month': ['2023-8', '2023-9', '2023-10', '2023-11', '2023-12', '2024-1', '2024-2', 
#               '2024-3', '2024-4', '2024-5', '2024-6', '2024-7', '2024-8', '2024-9', 
#               '2024-10', '2024-11', '2024-12', '2025-1', '2025-2', '2025-3', '2025-4', 
#               '2025-5', '2025-6', '2025-7'],
#     '5#': [0.00, 0.00, 0.26, 1.60, 3.81, 4.15, 3.93, 3.93, 4.20, 4.25, 3.26, 0.82, 
#            0.00, 0.00, 0.62, 0.82, 0.75, 3.86, 3.93, 4.31, 3.96, 3.53, 2.10, 0.00],
#     '6#': [0.00, 0.00, 0.11, 2.15, 2.96, 3.83, 4.03, 3.76, 4.08, 4.10, 3.76, 1.16, 
#            0.00, 0.00, 1.79, 0.02, 2.09, 3.24, 4.13, 4.12, 4.03, 3.96, 2.62, 0.00],
#     '25#': [0.00, 0.00, 0.00, 1.20, 2.10, 3.00, 4.01, 4.05, 3.70, 3.52, 0.53, 0.29, 
#             0.00, 0.00, 0.50, 1.00, 1.67, 3.21, 4.11, 4.08, 3.63, 3.46, 0.45, 0.39],
#     '19#': [0.00, 0.00, 1.46, 1.07, 2.72, 3.67, 3.91, 4.18, 4.24, 4.26, 3.68, 0.00, 
#             0.00, 0.00, 0.56, 0.20, 0.93, 2.97, 4.24, 4.29, 3.96, 3.77, 0.27, 0.00],
#     '21#': [0.00, 0.00, 0.00, 0.00, 0.90, 2.87, 3.21, 3.42, 3.29, 3.32, 0.91, 0.00, 
#             0.00, 0.00, 0.00, 0.00, 0.00, 0.95, 3.23, 3.38, 2.70, 1.26, 0.00, 0.00],
#     '27#': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.15, 2.56, 3.09, 3.30, 0.91, 0.00, 
#             0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 3.34, 3.32, 1.04, 0.62, 0.00, 0.00],
#     '28#': [0.00, 0.00, 0.00, 0.00, 0.00, 2.51, 3.30, 3.35, 3.74, 3.90, 1.60, 0.00, 
#             0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 3.39, 3.73, 3.48, 2.10, 1.62, 0.00],
#     '29#': [0.00, 0.00, 0.00, 0.00, 0.00, 2.57, 3.53, 3.50, 3.82, 4.05, 2.69, 0.00, 
#             0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 3.81, 3.90, 2.91, 2.76, 0.00, 0.00]
# }

def read_excel_to_dataframe(file_path, sheet_name=0):
    """
    读取Excel文件并将其转换为DataFrame
    
    参数:
    file_path (str): Excel文件的路径
    sheet_name (str/int): 工作表名称或索引，默认为第一个工作表
    
    返回:
    DataFrame: 包含Excel数据的DataFrame对象
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print("Excel文件读取成功！")
        return df
    except FileNotFoundError:
        print(f"错误：找不到文件 '{file_path}'")
        return None
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 指定Excel文件路径
    file_path = r"D:\vscodewenjian\pywenjian\积雪厚度20250905\积雪厚度20250905（1）.xlsx"  # 替换为你的Excel文件路径
    
    # 读取Excel文件
    df = read_excel_to_dataframe(file_path)
# 创建DataFrame
# df = pd.DataFrame(data)
df['month'] = pd.to_datetime(df['month'], format='%Y-%m')

# 获取所有列名（除了month）
columns = df.columns[1:]

# 图表名称列表
chart_names = [f'{col}雪崩'for col in columns
    
]

# 为每个数据列创建单独的图表
for i, col in enumerate(columns):
    # 使用预设的图表名称
    title = chart_names[i]
    
    # 创建新图表
    plt.figure(figsize=(14, 7))
    
    # 绘制当前列的数据
    plt.plot(df['month'], df[col], marker='o', linewidth=2, markersize=6, color='steelblue')
    
    # 在每个数据点上添加数值标签
    for j, (x, y) in enumerate(zip(df['month'], df[col])):
        if pd.notna(y):  # 只对非空值添加标签
            # 根据数值大小调整标签位置，避免重叠
            plt.annotate(f'{y:.2f}', 
                        (x, y),
                        textcoords="offset points",
                        xytext=(0, 10 if j % 2 == 0 else -15),  # 交替显示在上方和下方
                        ha='center',
                        fontsize=9,
                        #  bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7)
                        )
    
    # 设置图表标题和标签
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('积雪厚度（m）', fontsize=12)
    
    # 设置网格
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 旋转x轴标签以避免重叠
    plt.xticks(rotation=45)
    
    # 调整y轴范围，为数据标签留出空间
    y_min, y_max = plt.ylim()
    data_range = y_max - y_min
    plt.ylim(y_min - data_range * 0.1, y_max + data_range * 0.15)
    
    # 调整布局以确保所有元素都能显示
    plt.tight_layout()
    
    # 保存图表为图片文件
    filename = f"{save_dir}/{title.replace(' ', '_').replace('#', '号')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"已保存图表: {filename}")
    
    # 显示图表
    plt.show()

print(f"所有图表已生成完毕！已保存到 '{save_dir}' 文件夹中。")