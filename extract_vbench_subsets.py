import os
import json
import argparse
import glob

# 定义路径
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts_per_dimension")

# 读取11个txt文件，获取每个子集的数据

def read_prompts():
    prompts = {}
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith('.txt'):
            subset_name = os.path.splitext(filename)[0]
            with open(os.path.join(PROMPTS_DIR, filename), 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                prompts[subset_name] = lines
    return prompts

# 从压缩结果中提取子集

def extract_subsets(compress_dir, output_dir):
    # 读取原始prompts
    prompts = read_prompts()

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 创建kmeans和random二级目录
    kmeans_dir = os.path.join(output_dir, "kmeans")
    random_dir = os.path.join(output_dir, "random")
    os.makedirs(kmeans_dir, exist_ok=True)
    os.makedirs(random_dir, exist_ok=True)

    # 遍历所有子目录
    for root, dirs, files in os.walk(compress_dir):
        for file in files:
            if file.endswith('_ids.json'):
                json_path = os.path.join(root, file)
                with open(json_path, 'r', encoding='utf-8') as f:
                    selected_ids = json.load(f)

                # 确定是kmeans还是random
                if "representative" in root:
                    subset_dir = kmeans_dir
                elif "random" in root:
                    subset_dir = random_dir
                else:
                    continue

                # 提取子集名称
                base_name = os.path.splitext(file)[0]
                subset_name = base_name.replace('_ids', '')

                # 找到对应的metadata文件
                csv_file = os.path.join(root, f"{subset_name}.csv")
                if not os.path.exists(csv_file):
                    print(f"Warning: CSV file {csv_file} not found")
                    continue

                # 读取CSV文件，获取ID到prompt的映射
                id_to_prompt = {}
                with open(csv_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        header = lines[0].strip().split(',')
                        if 'id' in header:
                            id_idx = header.index('id')
                            for line in lines[1:]:
                                # 处理带引号的字段
                                import csv
                                reader = csv.reader([line])
                                parts = next(reader)
                                if len(parts) > id_idx:
                                    id_to_prompt[parts[id_idx]] = parts[id_idx]
                        else:
                            print(f"Warning: 'id' column not found in {csv_file}")
                            continue
                    else:
                        print(f"Warning: CSV file {csv_file} is empty")
                        continue

                # 提取选中的prompts
                selected_prompts = []
                for selected_id in selected_ids:
                    if selected_id in id_to_prompt:
                        selected_prompts.append(id_to_prompt[selected_id])
                    else:
                        print(f"  Warning: ID {selected_id} not found in CSV file")

                # 保存子集到新文件
                output_file = os.path.join(subset_dir, f"{subset_name}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    for prompt in selected_prompts:
                        f.write(prompt + '\n')

                # 打印详细信息
                print(f"Extracted {len(selected_prompts)} samples from {subset_name} to {output_file}")
                print(f"  Found {len(id_to_prompt)} entries in CSV file")
                print(f"  Found {len(selected_ids)} selected IDs in JSON file")
                # 检查是否有ID匹配
                if len(selected_prompts) == 0 and len(id_to_prompt) > 0 and len(selected_ids) > 0:
                    # 打印前几个ID进行比较
                    print(f"  First few CSV IDs: {list(id_to_prompt.keys())[:3]}")
                    print(f"  First few selected IDs: {selected_ids[:3]}")
                # 检查是否所有ID都匹配
                elif len(selected_prompts) == len(selected_ids):
                    print(f"  All selected IDs found in CSV file")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subsets from compression results")
    parser.add_argument("compress_dir", help="Directory containing compression results")
    parser.add_argument("output_dir", help="Directory to save extracted subsets")

    args = parser.parse_args()

    extract_subsets(args.compress_dir, args.output_dir)
    print(f"Subsets extracted successfully to {args.output_dir}")
