import json
import os
import sys
import argparse

def collect_case_names(prompts_dir):
    """收集所有case名称"""
    case_names = set()
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(prompts_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    case_name = line.strip()
                    if case_name:
                        case_names.add(case_name)
    return case_names

def filter_json_data(case_names, original_json_path):
    """筛选JSON数据"""
    with open(original_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    filtered_data = [item for item in data if item.get('prompt_en') in case_names]
    return data, filtered_data

def save_filtered_data(filtered_data, output_path):
    """保存筛选后的数据"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)

def main():
    # 使用argparse解析命令行参数
    parser = argparse.ArgumentParser(description='Filter VBench JSON data based on case names')
    parser.add_argument('prompts_directory', help='Directory containing prompt files')
    parser.add_argument('output_json', nargs='?', default='filtered_VBench.json', help='Output JSON file path')
    args = parser.parse_args()

    prompts_dir = args.prompts_directory
    output_path = args.output_json

    # 检查目录是否存在
    if not os.path.isdir(prompts_dir):
        print(f"Error: {prompts_dir} is not a directory")
        sys.exit(1)

    # 读取原始JSON文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    original_json_path = os.path.join(current_dir, "VBench_full_info.json")
    if not os.path.exists(original_json_path):
        print(f"Error: {original_json_path} does not exist")
        sys.exit(1)

    # 执行核心功能
    case_names = collect_case_names(prompts_dir)
    data, filtered_data = filter_json_data(case_names, original_json_path)
    save_filtered_data(filtered_data, output_path)

    # 输出结果
    print(f"Filtered {len(filtered_data)} elements out of {len(data)}")
    print(f"Output saved to {output_path}")

if __name__ == "__main__":
    main()
