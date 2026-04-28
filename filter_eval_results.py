import os
import json
import re
import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description='Filter eval results based on case names from prompts_per_dimension')
parser.add_argument('--prompts_dir', type=str, required=True, help='Path to prompts_per_dimension directory')
parser.add_argument('--input_dir', type=str, required=True, help='Path to directory containing eval_results.json files')
parser.add_argument('--output_dir', type=str, required=True, help='Path to output directory')
args = parser.parse_args()

# 创建输出目录
os.makedirs(args.output_dir, exist_ok=True)

# 收集所有case_name
all_case_names = set()
for filename in os.listdir(args.prompts_dir):
    if filename.endswith('.txt'):
        with open(os.path.join(args.prompts_dir, filename), 'r', encoding='utf-8') as f:
            for line in f:
                # 提取case_name（处理可能的行号和箭头）
                line = line.strip()
                if line:
                    # 检查是否有箭头符号
                    if '→' in line:
                        # 有箭头，提取箭头后面的内容
                        case_name = line.split('→')[1].strip()
                    else:
                        # 没有箭头，直接使用整行内容
                        case_name = line
                    all_case_names.add(case_name)

print(f"Collected {len(all_case_names)} case names from all prompt files")

# 处理每个eval_results.json文件
for filename in os.listdir(args.input_dir):
    if filename.endswith('eval_results.json'):
        input_file = os.path.join(args.input_dir, filename)
        output_file = os.path.join(args.output_dir, filename)

        # 读取json文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 处理每个维度
        for dimension, (_, cases) in data.items():
            filtered_cases = []
            scores = []

            # 过滤case
            for case in cases:
                video_path = case['video_path']
                # 提取case_name（匹配{case_name}-{num}.mp4格式）
                match = re.search(r'([^/]+)-\d+\.mp4$', video_path)
                if match:
                    case_name = match.group(1)
                    if case_name in all_case_names:
                        filtered_cases.append(case)
                        # 处理video_results得分
                        result = case['video_results']
                        if isinstance(result, bool):
                            score = 1.0 if result else 0.0
                        else:
                            score = result
                        scores.append(score)

            # 重新计算平均分
            if scores:
                avg_score = sum(scores) / len(scores)
                # 如果平均分大于1，除以100
                if avg_score > 1:
                    avg_score = avg_score / 100
            else:
                avg_score = 0.0

            # 更新数据
            data[dimension] = [avg_score, filtered_cases]
            print(f"Dimension '{dimension}': filtered {len(filtered_cases)} cases, average score: {avg_score}")

        # 保存修改后的json文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f'Processed {filename} and saved to {output_file}')

print('All files processed successfully!')