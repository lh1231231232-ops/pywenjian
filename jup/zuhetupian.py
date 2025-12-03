import os
import re
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict

def combine_images_with_dates(folder_path, output_folder, square_size=512):
    """
    合并相同编号的PNG文件，并在每个小图右下角添加日期水印
    
    参数:
    folder_path: 包含PNG文件的文件夹路径
    output_folder: 输出文件夹路径
    square_size: 输出图片的正方形尺寸(默认512x512)
    """
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 匹配文件名模式: 编号#_日期.png
    # pattern = re.compile(r'^(\d+)#_(\d{4}-\d{2}-\d{2})\.png$')
    pattern = re.compile(r'^[a-zA-Z]*?(\d+)#_(\d{4}-\d{2}-\d{2})\.png$')
    
    # 按编号分组文件
    file_groups = defaultdict(list)
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            # letter_prefix = match.group(1)
            number = match.group(1)
            date = match.group(2)
            file_groups[number].append((filename, date))
    
    # 如果没有找到匹配的文件
    if not file_groups:
        print("未找到符合命名模式的文件")
        return
    
    # 处理每个编号组的文件
    for number, files in file_groups.items():
        print(f"处理编号 {number} 的 {len(files)} 个文件")
        
        # 按日期排序
        files.sort(key=lambda x: x[1])
        
        # 读取所有图片并添加水印
        square_images = []
        for filename, date in files:
            try:
                img_path = os.path.join(folder_path, filename)
                img = Image.open(img_path).convert("RGBA")  # 确保图像有alpha通道
                
                # 将图片调整为正方形
                square_img = resize_to_square(img, square_size)
                
                # 根据图片大小自适应字体大小
                font_size = max(12, int(square_size * 0.1))  # 正方形尺寸的10%
                
                # 尝试加载字体
                font = None
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        # 尝试其他常见字体
                        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                    except:
                        # 使用默认字体
                        font = ImageFont.load_default()
                
                # 创建一个可以在图像上绘制的对象
                draw = ImageDraw.Draw(square_img)
                
                # 使用textbbox获取文本尺寸
                bbox = draw.textbbox((0, 0), date, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 计算文本位置(右下角，留一些边距)
                margin = max(5, int(square_size * 0.05))  # 正方形尺寸的5%
                position = (square_size - text_width - margin, square_size - text_height - margin)
                
                # 绘制文本(白色文本带有黑色背景以提高可读性)
                # 先绘制半透明黑色背景
                bg_position = (
                    position[0] - 2, 
                    position[1] - 2,
                    position[0] + text_width + 4,
                    position[1] + text_height + 4
                )
                draw.rectangle(bg_position, fill=(0, 0, 0, 180))  # 半透明黑色背景
                
                # 然后绘制白色文本
                draw.text(position, date, fill="white", font=font)
                
                square_images.append(square_img)
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {e}")
        
        if not square_images:
            continue
        
        # 计算大图的行列数
        num_images = len(square_images)
        cols = min(5, num_images)
        rows = (num_images + cols - 1) // cols
        
        # 创建新的大图
        combined_width = cols * square_size
        combined_height = rows * square_size
        combined_img = Image.new('RGBA', (combined_width, combined_height), (255, 255, 255, 255))
        
        # 将小图粘贴到大图上
        for i, img in enumerate(square_images):
            row = i // cols
            col = i % cols
            x = col * square_size
            y = row * square_size
            combined_img.paste(img, (x, y))
        
        # 保存合并后的图片到指定输出文件夹
        output_filename = f"{number}#.png"
        output_path = os.path.join(output_folder, output_filename)
        combined_img.save(output_path)
        print(f"已保存合并图片到: {output_path}")

def resize_to_square(img, size):
    """
    将图片调整为指定大小的正方形，保持原始比例
    
    参数:
    img: PIL Image对象
    size: 目标正方形大小
    
    返回:
    调整后的正方形图片
    """
    # 计算缩放比例
    width, height = img.size
    scale = min(size/width, size/height)
    
    # 计算新的尺寸
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # 缩放图片
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 创建正方形画布
    square_img = Image.new('RGBA', (size, size), (0, 0, 0, 255))
    
    # 将缩放后的图片粘贴到中心
    x_offset = (size - new_width) // 2
    y_offset = (size - new_height) // 2
    square_img.paste(resized_img, (x_offset, y_offset))
    
    return square_img

if __name__ == "__main__":
    # 使用示例
    folder_path = input("请输入包含PNG文件的文件夹路径: ").strip()
    output_folder = input("请输入输出文件夹路径: ").strip()
    
    # 询问用户是否要自定义正方形大小
    custom_size = input("请输入正方形图片大小(默认512，直接回车使用默认值): ").strip()
    square_size = 512  # 默认值
    if custom_size and custom_size.isdigit():
        square_size = int(custom_size)
        print(f"使用自定义大小: {square_size}x{square_size}")
    
    if os.path.isdir(folder_path):
        combine_images_with_dates(folder_path, output_folder, square_size)
        print("处理完成!")
    else:
        print("指定的输入路径不是有效文件夹")