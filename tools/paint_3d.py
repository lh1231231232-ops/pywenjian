import plotly.graph_objects as go
import numpy as np
import os

# 可配置的正方体透明度（0.0 - 1.0），修改此值以调整所有正方体的透明度
# 例如：0.0 完全透明，1.0 完全不透明。默认值设为 0.85 保持原来效果。
cube_opacity = 1

# 可配置的输出目录，支持相对路径或绝对路径。例如: 'output' 或 'D:/my_outputs'
# 将在保存前自动创建该目录（如果不存在）。
output_dir = r'D:\vscodewenjian\snow_worn_level'

# 是否在每个方块上显示标注（标注内容使用右上角图例信息）
# 手动设置为 True 来开启方块上显示文字标注
show_cube_labels = False
# 标注相对于方块中心在 z 方向上的偏移量（可调）
label_z_offset = 0.06

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

# 2. 遍历每一个数据点，为它们单独“画”一个正方体
for x_c, y_c, z_c in zip(X, Y, Z):
    # 以温升 (ΔT), 形变 (ΔS), 微震 (ΔP) 三个指标为基础，按用户指定规则判定整体预警等级
    vals = [int(x_c), int(y_c), int(z_c)]
    count_low = sum(1 for v in vals if v == 1)
    count_med = sum(1 for v in vals if v == 2)
    count_high = sum(1 for v in vals if v == 3)

    # 先判断最高级别（Ⅳ级 红色预警）
    if count_high >= 2 or (count_high == 1 and count_med == 2):
        danger = 'Ⅳ级 红色 (High)'
        color = 'red'
    # 其次判断Ⅲ级 橙色预警
    elif count_med >= 2 or (count_high == 1 and count_med == 1 and count_low == 1):
        danger = 'Ⅲ级 橙色 (Medium)'
        color = 'orange'
    # 再判断Ⅱ级 黄色预警（2或3个指标为低危险）
    elif count_low >= 2:
        danger = 'Ⅱ级 黄色 (Low)'
        color = 'yellow'
    # 否则视为安全/正常（绿色）
    else:
        danger = '正常 (Safe)'
        color = 'green'

    d = size / 2
    x_verts = [x_c-d, x_c+d, x_c+d, x_c-d, x_c-d, x_c+d, x_c+d, x_c-d]
    y_verts = [y_c-d, y_c-d, y_c+d, y_c+d, y_c-d, y_c-d, y_c+d, y_c+d]
    z_verts = [z_c-d, z_c-d, z_c-d, z_c-d, z_c+d, z_c+d, z_c+d, z_c+d]
    
    # 判断该等级是否已经添加过图例
    show_leg = danger not in seen_legends
    if show_leg:
        seen_legends.add(danger)

    # 将数值 1/2/3 映射为 ticktext 中的标签（低/中/高），hover 显示标签而非数字
    _label_map = {1: '低', 2: '中', 3: '高'}
    tx = _label_map.get(int(x_c), str(x_c))
    sy = _label_map.get(int(y_c), str(y_c))
    pz = _label_map.get(int(z_c), str(z_c))
    hover_text = f"<b>{danger}</b><br>温升 (ΔT): {tx}<br>形变 (ΔS): {sy}<br>微震 (ΔP): {pz}"

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

    # 可选：在方块上方显示标注（使用图例文本，即 cube['danger']）
    if show_cube_labels:
        lx, ly, lz = cube['center']
        # 将标签放置在方块顶部稍微偏高的位置
        lz = lz + (size / 2) + label_z_offset
        fig.add_trace(go.Scatter3d(
            x=[lx],
            y=[ly],
            z=[lz],
            mode='text',
            text=[cube['danger']],
            textfont=dict(size=12, color='black'),
            hoverinfo='none',
            showlegend=False
        ))

# 4. 调整坐标轴和整体布局
fig.update_layout(
    title='雪崩危险性 3D 预测模型 (正方体版)',
    scene=dict(
        # 设置轴标题和刻度的字体大小（title_size / tick_size）
        xaxis=dict(
            title=dict(text='温度 (Temperature)', font=dict(size=16)),
            tickvals=[1, 2, 3],
            ticktext=['低', '中', '高'],
            tickfont=dict(size=14),
            range=[0.5, 3.5],
            autorange='reversed'
        ), # 设置范围防止正方体贴边被切掉，且反向显示
        yaxis=dict(
            title=dict(text='形变 (Deformation)', font=dict(size=16)),
            tickvals=[1, 2, 3],
            ticktext=['低', '中', '高'],
            tickfont=dict(size=14),
            range=[0.5, 3.5]
        ),
        zaxis=dict(
            title=dict(text='振动 (Vibration)', font=dict(size=16)),
            tickvals=[1, 2, 3],
            ticktext=['低', '中', '高'],
            tickfont=dict(size=14),
            range=[0.5, 3.5]
        )
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