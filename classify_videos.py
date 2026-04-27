import os
import shutil
import argparse
import re

# 解析命令行参数
parser = argparse.ArgumentParser(description='Classify videos based on case names from prompt files')
parser.add_argument('video_dir', type=str, help='Directory containing videos')
parser.add_argument('output_dir', type=str, help='Output directory for classified videos')
args = parser.parse_args()

# 定义prompt文件目录（使用相对路径）
prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts_per_dimension')

# 遍历所有prompt文件
for filename in os.listdir(prompts_dir):
    if filename.endswith('.txt'):
        # 提取子集名称（不含.txt）
        subset_name = os.path.splitext(filename)[0]
        subset_dir = os.path.join(args.output_dir, subset_name)

        # 创建子集目录
        os.makedirs(subset_dir, exist_ok=True)

        # 读取prompt文件
        prompt_file = os.path.join(prompts_dir, filename)
        with open(prompt_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 提取case名称（去掉编号和箭头）
                case_name = line.strip().split('→')[1].strip()

                # 构建视频文件模式
                pattern = f"^{re.escape(case_name)}-0\d*\.mp4$"

                # 搜索匹配的视频文件
                for video_file in os.listdir(args.video_dir):
                    if re.match(pattern, video_file):
                        # 构建源路径和目标路径
                        src_path = os.path.join(args.video_dir, video_file)
                        dst_path = os.path.join(subset_dir, video_file)

                        # 复制视频文件
                        shutil.copy2(src_path, dst_path)
                        print(f"Copied {video_file} to {subset_dir}")

print("Video classification completed!")