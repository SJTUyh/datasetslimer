import os
import argparse
import csv

# 从压缩结果中提取子集

def extract_subsets(compress_dir, output_dir):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 创建kmeans和random二级目录
    kmeans_dir = os.path.join(output_dir, "kmeans")
    random_dir = os.path.join(output_dir, "random")
    os.makedirs(kmeans_dir, exist_ok=True)
    os.makedirs(random_dir, exist_ok=True)

    # 遍历所有子目录
    for root, dirs, files in os.walk(compress_dir):
        # 确定输出目录
        if "representative" in root:
            subset_dir = kmeans_dir
        elif "random" in root:
            subset_dir = random_dir
        else:
            continue

        # 处理该目录下的所有CSV文件
        for file in os.listdir(root):
            if file.endswith('.csv'):
                csv_path = os.path.join(root, file)

                # 提取子集名称（去掉.csv后缀）
                subset_name = os.path.splitext(file)[0]

                # 去掉metadata_前缀
                if subset_name.startswith('metadata_'):
                    original_subset_name = subset_name[len('metadata_'):]
                else:
                    original_subset_name = subset_name

                # 读取CSV文件并提取ID列
                selected_ids = []
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'id' in row:
                            selected_ids.append(row['id'])

                # 保存ID到txt文件
                output_file = os.path.join(subset_dir, f"{original_subset_name}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    for id_str in selected_ids:
                        f.write(id_str + '\n')

                # 打印信息
                print(f"Extracted {len(selected_ids)} samples from {subset_name} to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract subsets from compression results")
    parser.add_argument("compress_dir", help="Directory containing compression results")
    parser.add_argument("output_dir", help="Directory to save extracted subsets")

    args = parser.parse_args()

    extract_subsets(args.compress_dir, args.output_dir)
    print(f"Subsets extracted successfully to {args.output_dir}")
