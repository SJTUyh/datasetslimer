import os
import json
import argparse

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
    
    # 读取压缩结果
    for filename in os.listdir(compress_dir):
        if filename.endswith('.json'):
            json_path = os.path.join(compress_dir, filename)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理kmeans压缩结果
            if "kmeans" in filename:
                subset_dir = kmeans_dir
            # 处理随机压缩结果
            elif "random" in filename:
                subset_dir = random_dir
            else:
                continue
            
            # 提取子集名称
            subset_name = os.path.splitext(filename)[0]
            # 去掉前缀和后缀，获取原始子集名称
            if subset_name.startswith("kmeans_"):
                original_subset_name = subset_name[len("kmeans_"):]
            elif subset_name.startswith("random_"):
                original_subset_name = subset_name[len("random_"):]
            else:
                continue
            
            # 检查原始子集是否存在
            if original_subset_name not in prompts:
                print(f"Warning: Original subset {original_subset_name} not found in prompts")
                continue
            
            # 提取选中的索引
            selected_indices = data.get("selected_indices", [])
            
            # 从原始prompts中提取子集
            original_prompts = prompts[original_subset_name]
            selected_prompts = [original_prompts[i] for i in selected_indices if i < len(original_prompts)]
            
            # 保存子集到新文件
            output_file = os.path.join(subset_dir, f"{original_subset_name}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                for prompt in selected_prompts:
                    f.write(prompt + '\n')
            
            print(f"Extracted {len(selected_prompts)} samples from {original_subset_name} to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subsets from compression results")
    parser.add_argument("compress_dir", help="Directory containing compression results")
    parser.add_argument("output_dir", help="Directory to save extracted subsets")
    
    args = parser.parse_args()
    
    extract_subsets(args.compress_dir, args.output_dir)
    print(f"Subsets extracted successfully to {args.output_dir}")
