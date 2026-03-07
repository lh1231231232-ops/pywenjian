import plotly.graph_objects as go
import numpy as np
import os

# 可配置的正方体透明度（0.0 - 1.0），修改此值以调整所有正方体的透明度
# 例如：0.0 完全透明，1.0 完全不透明。默认值设为 0.85 保持原来效果。
cube_opacity = 0.5

# 可配置的输出目录，支持相对路径或绝对路径。例如: 'output' 或 'D:/my_outputs'
# 将在保存前自动创建该目录（如果不存在）。
output_dir = r'D:\vscodewenjian\snow_worn_level'

# 1. 准备数据：生成 3x3x3 的组合网格
levels = [1, 2, 3]
X, Y, Z = np.meshgrid(levels, levels, levels)
X = X.flatten()
Y = Y.flatten()
Z = Z.flatten()

fig = go.Figure()

# 用来控制图例（每种危险等级只在图例中显示一次）
seen_legends = set()

# 正方体的边长大小（0.4 可以让正方体之间留有空隙，如果是 1 则会拼成一个实心大魔方）
size = 0.7 

# 2. 遍历每一个数据点，为它们单独“画”一个正方体
for x_c, y_c, z_c in zip(X, Y, Z):
    # 模拟危险等级规则
    score = x_c + y_c + z_c
    if score <= 4:
        danger = '低危 (Low)'
        color = 'green'
    elif score <= 7:
        danger = '中危 (Medium)'
        color = 'orange'
    else:
        danger = '高危 (High)'
        color = 'red'
        
    # 计算正方体 8 个顶点的坐标
    d = size / 2
    x_verts = [x_c-d, x_c+d, x_c+d, x_c-d, x_c-d, x_c+d, x_c+d, x_c-d]
    y_verts = [y_c-d, y_c-d, y_c+d, y_c+d, y_c-d, y_c-d, y_c+d, y_c+d]
    z_verts = [z_c-d, z_c-d, z_c-d, z_c-d, z_c+d, z_c+d, z_c+d, z_c+d]
    
    # 判断该等级是否已经添加过图例
    show_leg = danger not in seen_legends
    seen_legends.add(danger)
    
    # 自定义鼠标悬停时显示的信息
    hover_text = f"<b>{danger}</b><br>温度: {x_c}<br>形变: {y_c}<br>振动: {z_c}"
    
    # 3. 使用 Mesh3d 添加正方体
    fig.add_trace(go.Mesh3d(
        x=x_verts,
        y=y_verts,
        z=z_verts,
        alphahull=0,       # 0 表示自动计算这 8 个点的凸包，从而自动拼成正方体
        color=color,
        opacity=cube_opacity,      # 使用可配置的 cube_opacity
        name=danger,
        legendgroup=danger, # 将相同危险等级的正方体绑定到同一个图例
        showlegend=show_leg,
        hoverinfo='text',
        text=[hover_text]*8 # 为 8 个顶点绑定相同的提示文本
    ))

# 4. 调整坐标轴和整体布局
fig.update_layout(
    title='雪崩危险性 3D 预测模型 (正方体版)',
    scene=dict(
        xaxis_title='温度 (Temperature)',
        yaxis_title='形变 (Deformation)',
        zaxis_title='振动 (Vibration)',
        xaxis=dict(tickvals=[1, 2, 3], ticktext=['一', '二', '三'], range=[0.5, 3.5], autorange='reversed'), # 设置范围防止正方体贴边被切掉，且反向显示
        yaxis=dict(tickvals=[1, 2, 3], ticktext=['一', '二', '三'], range=[0.5, 3.5]),
        zaxis=dict(tickvals=[1, 2, 3], ticktext=['一', '二', '三'], range=[0.5, 3.5])
    ),
    margin=dict(l=0, r=0, b=0, t=50)
)

# 5. 导出为交互式网页
html_filename = 'avalanche_3d_cubes.html'
# 确保输出目录存在并写入目标文件
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, html_filename)
fig.write_html(output_path)
print(f"包含正方体的 3D 交互网页已成功导出为: {os.path.abspath(output_path)}")