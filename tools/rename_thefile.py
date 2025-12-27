import os
import shutil

def batch_rename_files_advanced(directory, old_str, new_str, recursive=False, preview=False):
    """
    高级版批量重命名函数
    
    参数:
    directory: 要处理的目录路径
    old_str: 需要被替换的字符串
    new_str: 替换后的新字符串
    recursive: 是否递归处理子目录
    preview: 是否只预览而不实际执行重命名
    """
    # 检查目录是否存在
    if not os.path.exists(directory):
        print(f"错误: 目录 '{directory}' 不存在")
        return
    
    count = 0
    matched_files = []  # 存储匹配的文件路径
    
    # 遍历目录
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if old_str in filename:
                # 获取文件完整路径
                old_filepath = os.path.join(root, filename)
                matched_files.append(old_filepath)
                
                # 创建新文件名
                new_filename = filename.replace(old_str, new_str)
                new_filepath = os.path.join(root, new_filename)
                
                # 检查新文件名是否已存在
                if os.path.exists(new_filepath):
                    print(f"警告: 文件 '{new_filepath}' 已存在，跳过重命名 '{old_filepath}'")
                    continue
                
                # 预览模式只显示更改
                if preview:
                    print(f"[预览] 重命名: {old_filepath} -> {new_filepath}")
                else:
                    # 执行重命名
                    try:
                        os.rename(old_filepath, new_filepath)
                        print(f"重命名: {old_filepath} -> {new_filepath}")
                    except Exception as e:
                        print(f"错误: 无法重命名 {old_filepath} - {e}")
                        continue
                
                count += 1
        
        # 如果不递归处理子目录，跳出循环
        if not recursive:
            break
    
    mode = "预览" if preview else "实际"
    print(f"{mode}完成! 共处理了 {count} 个文件")
    
    return matched_files

def delete_previewed_files(files_list):
    """
    删除预览中显示的文件
    
    参数:
    files_list: 要删除的文件路径列表
    """
    if not files_list:
        print("没有文件需要删除")
        return
    
    print(f"\n以下 {len(files_list)} 个文件将被删除:")
    for file_path in files_list:
        print(f"  - {file_path}")
    
    # 确认删除
    confirm = input("\n确定要删除这些文件吗? 此操作不可恢复! (y/n): ")
    if confirm.lower() != 'y':
        print("删除操作已取消")
        return
    
    # 执行删除
    deleted_count = 0
    for file_path in files_list:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"已删除: {file_path}")
                deleted_count += 1
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"已删除文件夹: {file_path}")
                deleted_count += 1
        except Exception as e:
            print(f"错误: 无法删除 {file_path} - {e}")
    
    print(f"删除完成! 共删除了 {deleted_count} 个文件/文件夹")

if __name__ == "__main__":
    # 获取用户输入
    target_directory = input("请输入要处理的文件夹路径: ").strip()
    
    # 配置其他参数
    old_string = "07-19"
    new_string = "06-9"
    process_recursively = input("是否处理子目录? (y/n, 默认为n): ").strip().lower() == 'y'
    preview_only = input("是否只预览而不实际执行? (y/n, 默认为n): ").strip().lower() == 'y'
    
    # 先预览
    if preview_only:
        print("\n=== 预览模式 ===")
        matched_files = batch_rename_files_advanced(target_directory, old_string, new_string, process_recursively, True)
        
        # 询问是否删除预览的文件
        delete_choice = input("\n是否删除预览中显示的文件? (y/n): ").strip().lower()
        if delete_choice == 'y':
            delete_previewed_files(matched_files)
        else:
            # 确认是否执行重命名
            rename_choice = input("\n是否执行重命名? (y/n): ").strip().lower()
            if rename_choice == 'y':
                print("\n=== 执行重命名 ===")
                batch_rename_files_advanced(target_directory, old_string, new_string, process_recursively, False)
            else:
                print("操作已取消")
    else:
        # 直接执行
        print("\n=== 执行重命名 ===")
        batch_rename_files_advanced(target_directory, old_string, new_string, process_recursively, False)