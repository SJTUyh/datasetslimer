import os
import json
import csv
import glob

# 定义路径
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts_per_dimension")

# 读取11个txt文件，获取每个子集的数据id
def read_prompts():
    prompts = {}
    print(f"Reading prompts from: {PROMPTS_DIR}")
    if not os.path.exists(PROMPTS_DIR):
        print(f"Error: Prompts directory {PROMPTS_DIR} does not exist!")
        return prompts

    files = os.listdir(PROMPTS_DIR)
    print(f"Found {len(files)} files in prompts directory")

    for filename in files:
        if filename.endswith('.txt'):
            subset_name = os.path.splitext(filename)[0]
            file_path = os.path.join(PROMPTS_DIR, filename)
            print(f"Processing file: {filename}")
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                prompts[subset_name] = lines
                print(f"  Found {len(lines)} cases in {filename}")

    print(f"Total subsets: {len(prompts)}")
    return prompts

# 从evaluate结果文件夹中读取所有json文件
def read_eval_results(eval_dir, prompts):
    results = {}
    print(f"Reading evaluation results from: {eval_dir}")

    if not os.path.exists(eval_dir):
        print(f"Error: Evaluation directory {eval_dir} does not exist!")
        return results

    json_files = glob.glob(os.path.join(eval_dir, '*_eval_results.json'))
    print(f"Found {len(json_files)} json files")

    if not json_files:
        print("Warning: No json files found in evaluation directory")

    for json_file in json_files:
        print(f"Processing json file: {os.path.basename(json_file)}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # 提取分数含义（如dynamic_degree）
            for score_name, score_data in data.items():
                print(f"  Processing score type: {score_name}")
                if isinstance(score_data, list) and len(score_data) == 2:
                    avg_score, video_results = score_data
                    print(f"  Found {len(video_results)} video results")

                    for i, video_info in enumerate(video_results):
                        # 确保video_info是字典
                        if not isinstance(video_info, dict):
                            print(f"  Skipping video_info at index {i}: not a dictionary")
                            continue

                        video_path = video_info.get('video_path')
                        video_result = video_info.get('video_results')

                        if not video_path:
                            print(f"  Skipping video_info at index {i}: no video_path")
                            continue
                        if video_result is None:
                            print(f"  Skipping video_info at index {i}: no video_results")
                            continue

                        # 提取视频文件名
                        video_filename = os.path.basename(video_path)
                        print(f"  Processing video: {video_filename}")

                        # 分割文件名和扩展名
                        name, ext = os.path.splitext(video_filename)
                        # 检查扩展名是否为.mp4
                        if ext.lower() != '.mp4':
                            print(f"  Skipping: not an mp4 file")
                            continue

                        # 分割名称部分
                        name_parts = name.split('-')
                        # 检查是否有至少两部分（case_name和num）
                        if len(name_parts) < 2:
                            print(f"  Skipping: filename format incorrect, parts: {name_parts}")
                            continue

                        # 提取num部分
                        num_part = name_parts[-1]
                        # 检查num是否为0-4的数字
                        if not num_part.isdigit() or int(num_part) not in range(5):
                            print(f"  Skipping: invalid num part: {num_part}")
                            continue

                        # 提取case_name
                        case_name = '-'.join(name_parts[:-1])
                        print(f"  Extracted case_name: {case_name}")

                        # 检查case_name是否在prompts中
                        found = False
                        for subset_name, cases in prompts.items():
                            if case_name in cases:
                                found = True
                                subset_name = subset_name
                                break

                        if not found:
                            print(f"  Skipping: case_name not found in prompts")
                            continue

                        # 设置subset_name和data_id
                        subset_name = subset_name
                        data_id = case_name
                        print(f"  Matched subset: {subset_name}")

                        # 转换分数
                        if isinstance(video_result, bool):
                            score = 1 if video_result else 0
                        elif isinstance(video_result, (int, float)):
                            score = video_result
                            if score > 1:
                                score = score / 100
                        else:
                            # 处理其他类型，默认为0
                            score = 0
                        print(f"  Calculated score: {score}")

                        # 存储结果
                        if subset_name not in results:
                            results[subset_name] = {}
                        if data_id not in results[subset_name]:
                            results[subset_name][data_id] = {}
                        if score_name not in results[subset_name][data_id]:
                            results[subset_name][data_id][score_name] = []
                        results[subset_name][data_id][score_name].append(score)
                        print(f"  Stored score for {data_id}")

    # 计算每个数据id的平均分数
    print("\nCalculating average scores...")
    for subset_name, subset_data in results.items():
        print(f"  Processing subset: {subset_name}")
        for data_id, scores in subset_data.items():
            for score_name, score_list in scores.items():
                if score_list:
                    avg_score = sum(score_list) / len(score_list)
                    if avg_score > 1:
                        avg_score = avg_score / 100
                    results[subset_name][data_id][score_name] = avg_score
                    print(f"    {data_id}.{score_name}: {avg_score}")
                else:
                    results[subset_name][data_id][score_name] = 0

    print(f"\nTotal results: {len(results)} subsets")
    return results

# 生成metadata文件
def generate_metadata(eval_dir, output_dir):
    # 读取prompts和eval results
    print("\n=== Starting metadata generation ===")
    prompts = read_prompts()
    eval_results = read_eval_results(eval_dir, prompts)

    # 获取evaluate结果文件夹的名称
    eval_dir_name = os.path.basename(os.path.normpath(eval_dir))
    print(f"Evaluation directory name: {eval_dir_name}")

    # 准备info.json数据
    info_path = os.path.join(output_dir, "info.json")
    print(f"Info.json path: {info_path}")

    if os.path.exists(info_path):
        print("Found existing info.json, will update it")
        with open(info_path, 'r', encoding='utf-8') as f:
            info_data = json.load(f)
    else:
        print("No existing info.json, will create a new one")
        info_data = []

    # 创建info_data的字典版本，方便查找
    info_dict = {item['name']: item for item in info_data}
    print(f"Found {len(info_dict)} existing metadata entries")

    # 为每个子集生成metadata
    print(f"\nProcessing {len(prompts)} subsets...")
    for i, (subset_name, subset_prompts) in enumerate(prompts.items()):
        print(f"\n=== Processing subset {i+1}/{len(prompts)}: {subset_name} ===")
        metadata_name = f"metadata_{subset_name}"
        csv_path = os.path.join(output_dir, f"{metadata_name}.csv")
        print(f"CSV path: {csv_path}")

        # 收集该子集的所有分数
        subset_results = eval_results.get(subset_name, {})
        print(f"Found {len(subset_results)} results for this subset")

        # 确定该子集的所有分数类型
        score_names = set()
        for data_id, scores in subset_results.items():
            score_names.update(scores.keys())
        score_names = sorted(score_names)
        print(f"Score types: {score_names}")

        # 计算平均分数
        avg_scores = []
        if score_names:
            print("Calculating average scores...")
            for score_name in score_names:
                total = 0
                count = 0
                for data_id, scores in subset_results.items():
                    if score_name in scores:
                        total += scores[score_name]
                        count += 1
                if count > 0:
                    avg = total / count
                    avg_scores.append(avg)
                    print(f"  {score_name}: {avg}")
                else:
                    avg_scores.append(0)
                    print(f"  {score_name}: 0 (no data)")

        # 检查CSV文件是否存在
        if os.path.exists(csv_path):
            print("Found existing CSV file, will update it")
            # 读取现有CSV文件
            existing_rows = []
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                existing_fieldnames = reader.fieldnames
                for row in reader:
                    existing_rows.append(row)
            print(f"Found {len(existing_rows)} existing rows")

            # 生成新的特征名称
            new_feature_names = [f"{eval_dir_name}/{score_name}" for score_name in score_names]
            print(f"New feature names: {new_feature_names}")

            # 检查新特征是否已存在
            for feature_name in new_feature_names:
                if feature_name and feature_name not in existing_fieldnames:
                    existing_fieldnames.append(feature_name)
                    print(f"Added new feature: {feature_name}")

            # 确保difficulty列位于最后
            if 'difficulty' in existing_fieldnames:
                existing_fieldnames.remove('difficulty')
                existing_fieldnames.append('difficulty')

            # 清理字段名，移除None值
            existing_fieldnames = [field for field in existing_fieldnames if field is not None]
            print(f"Cleaned fieldnames: {existing_fieldnames}")

            # 更新现有行
            print("Updating existing rows...")
            for row in existing_rows:
                # 清理行中的None字段
                row = {k: v for k, v in row.items() if k is not None}

                data_id = row.get('id', 'unknown')
                print(f"  Processing row: {data_id}")
                for k, score_name in enumerate(score_names):
                    feature_name = new_feature_names[k]
                    if not feature_name:
                        continue
                    # 尝试匹配视频文件名中的prompt部分
                    matched = False
                    for video_id, scores in subset_results.items():
                        # 直接使用完整的video_id作为prompt
                        if video_id in data_id:
                            if score_name in scores:
                                row[feature_name] = scores[score_name]
                                matched = True
                                print(f"    Matched {score_name}: {scores[score_name]}")
                            break
                    if not matched:
                        row[feature_name] = 0
                        print(f"    No match for {score_name}, setting to 0")

            # 写入更新后的CSV文件
            print("Writing updated CSV file...")
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                # 使用 quoting=csv.QUOTE_NONE 避免添加引号
                writer = csv.DictWriter(csvfile, fieldnames=existing_fieldnames, quoting=csv.QUOTE_NONE, escapechar='\\')
                writer.writeheader()
                for row in existing_rows:
                    # 确保row只包含fieldnames中的字段
                    filtered_row = {k: v for k, v in row.items() if k in existing_fieldnames}
                    writer.writerow(filtered_row)
        else:
            print("No existing CSV file, will create a new one")
            # 生成新的CSV文件
            new_feature_names = [f"{eval_dir_name}/{score_name}" for score_name in score_names]
            fieldnames = ['id'] + new_feature_names + ['difficulty']
            print(f"Fieldnames: {fieldnames}")

            # 清理字段名，移除None值
            fieldnames = [field for field in fieldnames if field is not None]
            print(f"Cleaned fieldnames: {fieldnames}")

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                # 使用 quoting=csv.QUOTE_NONE 避免添加引号
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_NONE, escapechar='\\')
                writer.writeheader()

                print(f"Writing {len(subset_prompts)} rows...")
                for j, prompt in enumerate(subset_prompts):
                    # 使用prompt作为id，确保与txt文件中的每一行相同
                    data_id = prompt
                    print(f"  Writing row {j+1}/{len(subset_prompts)}: {data_id}")

                    # 构建行数据
                    row = {'id': data_id}
                    for k, score_name in enumerate(score_names):
                        feature_name = new_feature_names[k]
                        if not feature_name:
                            continue
                        # 尝试匹配视频文件名中的prompt部分
                        matched = False
                        for video_id, scores in subset_results.items():
                            # 直接使用完整的video_id作为prompt
                            if video_id in data_id:
                                if score_name in scores:
                                    row[feature_name] = scores[score_name]
                                    matched = True
                                    print(f"    Matched {score_name}: {scores[score_name]}")
                                break
                        if not matched:
                            row[feature_name] = 0
                            print(f"    No match for {score_name}, setting to 0")
                    # 简化处理，难度级别设为level0
                    row['difficulty'] = 'level0'

                    # 确保row只包含fieldnames中的字段
                    filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                    writer.writerow(filtered_row)

        # 更新info.json
        print("Updating info.json...")
        if metadata_name in info_dict:
            # 现有条目，添加新的平均分数
            info_dict[metadata_name]['avg_scores'].extend(avg_scores)
            print(f"Updated existing entry for {metadata_name}")
        else:
            # 新条目
            info_dict[metadata_name] = {
                "name": metadata_name,
                "count": len(subset_prompts),
                "avg_scores": avg_scores,
                "difficulty_map": {
                    "level0": 0
                }
            }
            print(f"Created new entry for {metadata_name}")

    # 生成info.json
    info_data = list(info_dict.values())
    print(f"Writing info.json with {len(info_data)} entries...")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert VBench evaluate results to metadata format")
    parser.add_argument("eval_dir", help="Directory containing VBench evaluate results")
    parser.add_argument("output_dir", help="Directory to save metadata files")

    args = parser.parse_args()

    # 确保输出目录存在
    print(f"Output directory: {args.output_dir}")
    os.makedirs(args.output_dir, exist_ok=True)

    generate_metadata(args.eval_dir, args.output_dir)
    print(f"\n=== Metadata generated successfully in {args.output_dir} ===")