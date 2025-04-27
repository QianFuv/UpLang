import orjson
import os

def update_language_file(old_file_path, new_file_path, output_path=None, indent=False):
    """
    更新Minecraft模组语言文件，通过与新版本比较。
    
    此函数比较两个JSON语言文件，保持新文件的结构同时保留旧文件中已有的翻译。
    
    参数:
        old_file_path (str): 旧语言文件的路径
        new_file_path (str): 新语言文件的路径
        output_path (str, optional): 保存更新文件的路径。若为 None，则覆盖旧文件。
        indent (bool, optional): 是否使用 2 个空格缩进输出的 JSON。默认为 False。
    
    返回:
        dict: 更新后的语言数据
    """
    # 如果未指定 output_path，则覆盖旧文件
    if output_path is None:
        output_path = old_file_path
    
    # 配置序列化选项
    dump_options = 0
    if indent:
        dump_options |= orjson.OPT_INDENT_2
    
    # 读取旧文件
    with open(old_file_path, 'rb') as old_file:
        old_data = orjson.loads(old_file.read())
    
    # 读取新文件
    with open(new_file_path, 'rb') as new_file:
        new_data = orjson.loads(new_file.read())
    
    # 创建一个具有新数据结构的更新字典
    updated_data = {}
    
    # 仅包含新文件中的键
    for key in new_data:
        # 如果键存在于旧文件中，保留旧值
        if key in old_data:
            updated_data[key] = old_data[key]
        # 否则，使用新文件中的值
        else:
            updated_data[key] = new_data[key]
    
    # 如需要，为输出文件创建目录
    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 将更新后的数据写入输出文件
    with open(output_path, 'wb') as output_file:
        output_file.write(orjson.dumps(updated_data, option=dump_options))
    
    return updated_data