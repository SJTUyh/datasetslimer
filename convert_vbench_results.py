import os
import json
import csv
import glob

# 定义路径
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts_per_dimension")

# 读取11个txt文件，获取每个子集的数据id
def read_prompts():
    prompts = {}
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith('.txt'):
            subset_name = os.path.splitext(filename)[0]
            with open(os.path.join(PROMPTS_DIR, filename), 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                prompts[subset_name] = lines
    return prompts

# 从evaluate结果文件夹中读取所有json文件
def read_eval_results(eval_dir, prompts):
    results = {}
    # 匹配所有的json文件，包括test_eval_results.json、test_eval_results1.json等
    json_files = glob.glob(os.path.join(eval_dir, '*.json'))

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # 提取分数含义（如dynamic_degree）
            if isinstance(data, dict):
                for score_name, score_data in data.items():
                    if isinstance(score_data, list) and len(score_data) == 2:
                        avg_score, video_results = score_data

                        for video_info in video_results:
                            # 确保video_info是字典
                            if isinstance(video_info, dict):
                                video_path = video_info.get('video_path')
                                video_result = video_info.get('video_results')
                                if video_path and video_result:
                                    # 提取子集名称
                                    # 处理不同系统的路径分隔符
                                    parts = video_path.split('/')
                                    subset_name = None
                                    for part in parts:
                                        if part in prompts:
                                            subset_name = part
                                            break

                                    if subset_name:
                                        # 提取数据id（视频文件名）
                                        video_filename = os.path.basename(video_path)
                                        # 去掉文件扩展名和数字后缀
                                        data_id = os.path.splitext(video_filename)[0]
                                        # 去掉末尾的数字，比如 "prompt-0" 变成 "prompt"
                                        if '-' in data_id:
                                            data_id = '-'.join(data_id.split('-')[:-1])

                                        # 转换分数
                                        if isinstance(video_result, bool):
                                            score = 1 if video_result else 0
                                        else:
                                            score = video_result

                                        # 存储结果
                                        if subset_name not in results:
                                            results[subset_name] = {}
                                        if data_id not in results[subset_name]:
                                            results[subset_name][data_id] = {}
                                        if score_name not in results[subset_name][data_id]:
                                            results[subset_name][data_id][score_name] = []
                                        results[subset_name][data_id][score_name].append(score)
            elif isinstance(data, list):
                # 处理data是列表的情况
                for item in data:
                    if isinstance(item, dict):
                        for score_name, score_data in item.items():
                            if isinstance(score_data, list) and len(score_data) == 2:
                                avg_score, video_results = score_data

                                for video_info in video_results:
                                    # 确保video_info是字典
                                    if isinstance(video_info, dict):
                                        video_path = video_info.get('video_path')
                                        video_result = video_info.get('video_results')
                                        if video_path and video_result:
                                            # 提取子集名称
                                            # 处理不同系统的路径分隔符
                                            parts = video_path.split('/')
                                            subset_name = None
                                            for part in parts:
                                                if part in prompts:
                                                    subset_name = part
                                                    break

                                            if subset_name:
                                                # 提取数据id（视频文件名）
                                                video_filename = os.path.basename(video_path)
                                                # 去掉文件扩展名和数字后缀
                                                data_id = os.path.splitext(video_filename)[0]
                                                # 去掉末尾的数字，比如 "prompt-0" 变成 "prompt"
                                                if '-' in data_id:
                                                    data_id = '-'.join(data_id.split('-')[:-1])

                                                # 转换分数
                                                if isinstance(video_result, bool):
                                                    score = 1 if video_result else 0
                                                else:
                                                    score = video_result

                                                # 存储结果
                                                if subset_name not in results:
                                                    results[subset_name] = {}
                                                if data_id not in results[subset_name]:
                                                    results[subset_name][data_id] = {}
                                                if score_name not in results[subset_name][data_id]:
                                                    results[subset_name][data_id][score_name] = []
                                                results[subset_name][data_id][score_name].append(score)

    # 计算每个数据id的平均分数
    for subset_name, subset_data in results.items():
        for data_id, scores in subset_data.items():
            for score_name, score_list in scores.items():
                if score_list:
                    results[subset_name][data_id][score_name] = sum(score_list) / len(score_list)
                else:
                    results[subset_name][data_id][score_name] = 0

    return results

# 生成metadata文件
def generate_metadata(eval_dir, output_dir):
    # 读取prompts和eval results
    prompts = read_prompts()
    eval_results = read_eval_results(eval_dir, prompts)

    # 获取evaluate结果文件夹的名称
    eval_dir_name = os.path.basename(eval_dir)

    # 准备info.json数据
    info_data = []

    # 为每个子集生成metadata
    for i, (subset_name, subset_prompts) in enumerate(prompts.items()):
        metadata_name = f"metadata_{subset_name}"
        csv_path = os.path.join(output_dir, f"{metadata_name}.csv")

        # 收集该子集的所有分数
        subset_results = eval_results.get(subset_name, {})

        # 确定该子集的所有分数类型
        score_names = set()
        for data_id, scores in subset_results.items():
            score_names.update(scores.keys())
        score_names = sorted(score_names)

        # 计算平均分数
        avg_scores = []
        if score_names:
            for score_name in score_names:
                total = 0
                count = 0
                for data_id, scores in subset_results.items():
                    if score_name in scores:
                        total += scores[score_name]
                        count += 1
                if count > 0:
                    avg_scores.append(total / count)
                else:
                    avg_scores.append(0)

        # 生成CSV文件
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            # 使用evaluate结果文件夹名称+分数含义作为特征名称，用/连接
            fieldnames = ['id'] + [f"{eval_dir_name}/{score_name}" for score_name in score_names] + ['difficulty']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # 为每个prompt生成一行数据
            for j, prompt in enumerate(subset_prompts):
                # 使用prompt作为id，确保与txt文件中的每一行相同
                data_id = prompt

                # 构建行数据
                row = {'id': data_id}
                for k, score_name in enumerate(score_names):
                    # 初始化分数为0
                    row[f"{eval_dir_name}/{score_name}"] = 0

                    # 尝试匹配视频文件名中的prompt部分
                    for video_id, scores in subset_results.items():
                        # 视频文件名格式可能是 "prompt-0.mp4"，去掉后缀和数字
                        video_prompt = video_id.split('-')[0]

                        # 对于所有子集，使用更宽松的匹配方式
                        prompt_core = data_id.split(',')[0].strip() if ',' in data_id else data_id.strip()
                        # 使用更宽松的匹配方式，转换为小写并去除多余的空格
                        if video_prompt.strip().lower() in prompt_core.lower() or prompt_core.lower() in video_prompt.strip().lower():
                            if score_name in scores:
                                row[f"{eval_dir_name}/{score_name}"] = scores[score_name]
                                break

                # 简化处理，难度级别设为level0
                row['difficulty'] = 'level0'

                writer.writerow(row)

        # 添加到info.json
        info_data.append({
            "name": metadata_name,
            "count": len(subset_prompts),
            "avg_scores": avg_scores,
            "difficulty_map": {
                "level0": 0
            }
        })

    # 生成info.json
    info_path = os.path.join(output_dir, "info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert VBench evaluate results to metadata format")
    parser.add_argument("eval_dir", help="Directory containing VBench evaluate results")
    parser.add_argument("output_dir", help="Directory to save metadata files")

    args = parser.parse_args()

    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    generate_metadata(args.eval_dir, args.output_dir)
    print(f"Metadata generated successfully in {args.output_dir}")