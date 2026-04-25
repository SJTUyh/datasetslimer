import os
import json
import argparse
import csv

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
        # 处理representative目录（kmeans压缩）
        if "representative" in root:
            subset_dir = kmeans_dir
            # 处理该目录下的所有文件
            process_subset(root, subset_dir, prompts)
        # 处理random目录（随机压缩）
        elif "random" in root:
            subset_dir = random_dir
            # 处理该目录下的所有文件
            process_subset(root, subset_dir, prompts)

# 处理单个子目录

def process_subset(root, subset_dir, prompts):
    # 找到所有的_ids.json文件
    for file in os.listdir(root):
        if file.endswith('_ids.json'):
            json_path = os.path.join(root, file)
            with open(json_path, 'r', encoding='utf-8') as f:
                selected_indices = json.load(f)

            # 提取子集名称
            base_name = os.path.splitext(file)[0]
            subset_name = base_name.replace('_ids', '')

            # 找到对应的原始子集名称
            # 去掉metadata_前缀
            if subset_name.startswith('metadata_'):
                original_subset_name = subset_name[len('metadata_'):]
            else:
                original_subset_name = subset_name

            # 检查原始子集是否存在
            if original_subset_name not in prompts:
                print(f"Warning: Original subset {original_subset_name} not found in prompts")
                continue

            # 从原始prompts中提取子集
            original_prompts = prompts[original_subset_name]
            selected_prompts = []
            for idx in selected_indices:
                idx = int(idx)  # 转换为整数
                if idx < len(original_prompts):
                    selected_prompts.append(original_prompts[idx])
                else:
                    print(f"  Warning: Index {idx} out of range for {original_subset_name}")

            # 保存子集到新文件
            output_file = os.path.join(subset_dir, f"{original_subset_name}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                for prompt in selected_prompts:
                    f.write(prompt + '\n')

            # 打印详细信息
            print(f"Extracted {len(selected_prompts)} samples from {original_subset_name} to {output_file}")
            print(f"  Original subset has {len(original_prompts)} samples")
            print(f"  Selected indices: {selected_indices}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subsets from compression results")
    parser.add_argument("compress_dir", help="Directory containing compression results")
    parser.add_argument("output_dir", help="Directory to save extracted subsets")

    args = parser.parse_args()

    extract_subsets(args.compress_dir, args.output_dir)
    print(f"Subsets extracted successfully to {args.output_dir}")
