import json
import os
import sys

def main():
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("Usage: python filter_json.py <prompts_directory>")
        sys.exit(1)

    prompts_dir = sys.argv[1]
    if not os.path.isdir(prompts_dir):
        print(f"Error: {prompts_dir} is not a directory")
        sys.exit(1)

    # 收集所有case名称
    case_names = set()
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(prompts_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    case_name = line.strip()
                    if case_name:
                        case_names.add(case_name)

    # 读取原始JSON文件
    # 使用相对路径，基于当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    original_json_path = os.path.join(current_dir, "VBench_full_info.json")
    if not os.path.exists(original_json_path):
        print(f"Error: {original_json_path} does not exist")
        sys.exit(1)

    with open(original_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 筛选元素
    filtered_data = [item for item in data if item.get('prompt_en') in case_names]

    # 输出到新的JSON文件
    output_path = "filtered_VBench.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)

    print(f"Filtered {len(filtered_data)} elements out of {len(data)}")
    print(f"Output saved to {output_path}")

if __name__ == "__main__":
    main()
