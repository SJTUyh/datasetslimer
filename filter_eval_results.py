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

# 构建case_name到维度的映射
case_names_by_dimension = {}
for filename in os.listdir(args.prompts_dir):
    if filename.endswith('.txt'):
        dimension = filename[:-4]  # 去掉.txt后缀
        case_names = []
        with open(os.path.join(args.prompts_dir, filename), 'r', encoding='utf-8') as f:
            for line in f:
                # 提取case_name（去掉行号和箭头）
                if '→' in line:
                    case_name = line.split('→')[1].strip()
                    case_names.append(case_name)
        case_names_by_dimension[dimension] = set(case_names)

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
            if dimension not in case_names_by_dimension:
                print(f"Warning: Dimension '{dimension}' not found in prompts_per_dimension directory")
                continue
            
            valid_case_names = case_names_by_dimension[dimension]
            filtered_cases = []
            scores = []
            
            # 过滤case
            for case in cases:
                video_path = case['video_path']
                # 提取case_name（匹配{case_name}-{num}.mp4格式）
                match = re.search(r'([^/]+)-\d+\.mp4$', video_path)
                if match:
                    case_name = match.group(1)
                    if case_name in valid_case_names:
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