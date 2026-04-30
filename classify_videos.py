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

        # 初始化统计字典，记录匹配0-5个视频的case数量
        match_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # 读取prompt文件
        prompt_file = os.path.join(prompts_dir, filename)
        with open(prompt_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 提取case名称
                case_name = line.strip()

                # 统计匹配的视频数量
                matched_videos = 0

                # 构建视频文件模式
                pattern = f"^{re.escape(case_name)}-([0-4])\.mp4$"

                # 搜索匹配的视频文件
                for video_file in os.listdir(args.video_dir):
                    if re.match(pattern, video_file):
                        # 构建源路径和目标路径
                        src_path = os.path.join(args.video_dir, video_file)
                        dst_path = os.path.join(subset_dir, video_file)

                        # 复制视频文件
                        shutil.copy2(src_path, dst_path)
                        #print(f"Copied {video_file} to {subset_dir}")
                        matched_videos += 1

                # 更新统计字典
                if matched_videos > 5:
                    matched_videos = 5
                match_counts[matched_videos] += 1

        # 输出统计结果
        print(f"\n统计结果 - {filename}:")
        print("匹配视频数 | Case数量")
        print("-----------|----------")
        for count in range(6):
            print(f"{count:10} | {match_counts[count]:10}")

print("\nVideo classification completed!")