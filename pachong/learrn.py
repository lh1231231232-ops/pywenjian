import matplotlib.pyplot as plt

# 修复中文显示（Windows），并保证负号正常显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 或改为 ['Microsoft YaHei'] 根据系统字体调整
plt.rcParams['axes.unicode_minus'] = False

# 数据
layers = [
    ("强风化中粗粒二云二长花岗岩", 1, 2324.15),
    ("中风化中粗粒二云二长花岗岩", 2.6, 2321.55),
    ("弱风化中粗粒二云二长花岗岩", 3.22, 2318.33)
]

# 提取信息
labels = [layer[0] for layer in layers]
thicknesses = [layer[1] for layer in layers]
bottom_elevations = [layer[2] for layer in layers]

# 计算每一层的顶部标高（如果需要显示）
top_elevations = [bottom + thickness for bottom, thickness in zip(bottom_elevations, thicknesses)]

# 创建垂直柱状图（X 为层名，Y 为厚度）
fig, ax = plt.subplots(figsize=(10, 6))
x = range(len(layers))
bars = ax.bar(x, thicknesses, color='skyblue', edgecolor='k', linewidth=0.5)

# 添加顶底标注（顶标高和底标高），放在柱子上方和下方
for xi, thick, bottom, top in zip(x, thicknesses, bottom_elevations, top_elevations):
    ax.text(xi, thick + 0.05, f'顶: {top:.2f} m', ha='center', va='bottom', fontsize=9)
    ax.text(xi, 0 - 0.05 * max(thicknesses), f'底: {bottom:.2f} m', ha='center', va='top', fontsize=9)

# 设置坐标标签（已交换：X 为层名，Y 为厚度）
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=30, ha='right')
ax.set_xlabel('岩层名称')
ax.set_ylabel('厚度 (m)')
ax.set_title('钻孔柱状图（垂直柱）')

plt.tight_layout()
plt.show()
