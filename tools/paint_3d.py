import plotly.graph_objects as go
import numpy as np
import os

# 可配置的正方体透明度（0.0 - 1.0），修改此值以调整所有正方体的透明度
# 例如：0.0 完全透明，1.0 完全不透明。默认值设为 0.85 保持原来效果。
cube_opacity = 1

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
size = 0.5 

# 收集所有正方体数据，后面按视点深度排序（Painter's algorithm）再绘制
cubes = []

# 2. 遍历每一个数据点，准备正方体数据
for x_c, y_c, z_c in zip(X, Y, Z):
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

    d = size / 2
    x_verts = [x_c-d, x_c+d, x_c+d, x_c-d, x_c-d, x_c+d, x_c+d, x_c-d]
    y_verts = [y_c-d, y_c-d, y_c+d, y_c+d, y_c-d, y_c-d, y_c+d, y_c+d]
    z_verts = [z_c-d, z_c-d, z_c-d, z_c-d, z_c+d, z_c+d, z_c+d, z_c+d]

    show_leg = danger not in seen_legends
    if show_leg:
        seen_legends.add(danger)

    hover_text = f"<b>{danger}</b><br>温度: {x_c}<br>形变: {y_c}<br>振动: {z_c}"

    cubes.append({
        'center': (x_c, y_c, z_c),
        'x': x_verts,
        'y': y_verts,
        'z': z_verts,
        'color': color,
        'hover': hover_text,
        'danger': danger,
        'showlegend': show_leg
    })

# 定义视点（可调整），用于按深度排序
camera_eye = dict(x=1.8, y=1.8, z=1.2)

# 计算深度并排序（点乘视点向量，值小的先绘制）
def depth_of(cube, eye=camera_eye):
    # 使用所有顶点计算深度，取最小的点乘值作为该立方体的“最远深度”，
    # 保证更可靠的从远到近排序（避免中心点排序带来的遮挡问题）。
    xs = cube['x']
    ys = cube['y']
    zs = cube['z']
    depths = [xx * eye['x'] + yy * eye['y'] + zz * eye['z'] for xx, yy, zz in zip(xs, ys, zs)]
    return min(depths)

cubes.sort(key=depth_of)

# 绘制按深度排序后的正方体（从远到近），并为每个 Mesh3d 添加简单光照与平面着色
for cube in cubes:
    # 使用显式三角面定义（12 个三角，6 个面），确保每个面的透明度一致
    # 顶点顺序与之前保持一致（0..7）
# 正确的 12 个三角形面（6 个正方形面，每个面 2 个三角形完美拼接）
    i = [0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 2, 6]
    k = [2, 3, 6, 7, 5, 4, 6, 7, 7, 4, 6, 5]

    fig.add_trace(go.Mesh3d(
        x=cube['x'],
        y=cube['y'],
        z=cube['z'],
        i=i,
        j=j,
        k=k,
        color=cube['color'],
        opacity=cube_opacity,
        name=cube['danger'],
        legendgroup=cube['danger'],
        showlegend=cube['showlegend'],
        hoverinfo='text',
        text=[cube['hover']]*8,
        # 去掉光照/阴影效果，使用默认平面渲染
        flatshading=False
    ))

    # 绘制边缘线以增强立体感
    # 将 12 条边用 None 分隔组成一条折线序列
    edges_x = []
    edges_y = []
    edges_z = []
    v = list(zip(cube['x'], cube['y'], cube['z']))
    edge_idx = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    for a,b in edge_idx:
        xa, ya, za = v[a]
        xb, yb, zb = v[b]
        edges_x += [xa, xb, None]
        edges_y += [ya, yb, None]
        edges_z += [za, zb, None]

    fig.add_trace(go.Scatter3d(
        x=edges_x,
        y=edges_y,
        z=edges_z,
        mode='lines',
        line=dict(color='black', width=1),
        hoverinfo='none',
        showlegend=False
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
        ,
        camera=dict(eye=camera_eye)
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