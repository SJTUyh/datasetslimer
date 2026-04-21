import argparse
import json
import random
import csv
import os
import string
import numpy as np


def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def generate_difficulty_map(max_dimension):
    dimensions = random.randint(1, max_dimension)
    return {f"level{i}": i for i in range(dimensions)}


def generate_avg_scores(num_score_types, max_avg):
    return [round(random.uniform(0, max_avg), 2) for _ in range(num_score_types)]


def generate_info(num_subsets, max_dimension, max_avg, num_score_types):
    info = []
    for i in range(num_subsets):
        difficulty_map = generate_difficulty_map(max_dimension)
        info.append({
            'name': f'random_metadata{i}',
            'count': 0,
            'avg_scores': generate_avg_scores(num_score_types, max_avg),
            'difficulty_map': difficulty_map
        })
    return info


def generate_csv_file(file_path, subset_info, case_range, score_types, binary_scores=False):
    # 如果 subset_info 中已经有 count，则使用它；否则随机生成
    if 'count' in subset_info and subset_info['count'] > 0:
        num_cases = subset_info['count']
    else:
        num_cases = random.randint(case_range[0], case_range[1])
    difficulty_map = subset_info['difficulty_map']
    avg_scores = subset_info['avg_scores']
    difficulties = list(difficulty_map.keys())

    fieldnames = ['id'] + score_types + ['difficulty']

    rows = []
    for _ in range(num_cases):
        row = {
            'id': generate_random_string(random.randint(6, 12))
        }

        difficulty = random.choice(difficulties)

        for i, score in enumerate(score_types):
            if binary_scores:
                row[score] = 1 if random.random() < avg_scores[i] else 0
            else:
                row[score] = round(np.clip(random.normalvariate(avg_scores[i], 0.15), 0, 1), 2)

        row['difficulty'] = difficulty
        rows.append(row)

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return num_cases


def main():
    parser = argparse.ArgumentParser(description='Generate metadata subsets')
    parser.add_argument('--info_file', type=str, help='Path to existing info.json file to use (if specified, other generation params are ignored)')
    parser.add_argument('--num_subsets', type=int, default=3, help='Number of subsets to generate (default: 3)')
    parser.add_argument('--max_dimension', type=int, default=3, help='Max dimension for difficulty_map (default: 3)')
    parser.add_argument('--max_avg', type=float, default=0.5, help='Maximum average score (default: 0.5)')
    parser.add_argument('--case_range', type=int, nargs=2, default=[100, 200], help='Case count range [min, max] (default: 100 200)')
    parser.add_argument('--score_types', type=str, nargs='+', default=['score0', 'score1', 'score2'], help='Score column names (default: score0 score1 score2)')
    parser.add_argument('--output_dir', type=str, default='./generated_data', help='Output directory (default: ./generated_data)')
    parser.add_argument('--binary_scores', action='store_true', help='Generate binary scores (0 or 1) instead of continuous scores (0~1)')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.info_file:
        with open(args.info_file, 'r', encoding='utf-8') as f:
            info = json.load(f)
        print(f'Loaded info from {args.info_file}')

        for subset in info:
            csv_path = os.path.join(args.output_dir, f'{subset["name"]}.csv')
            # 根据 avg_scores 长度自动确定 score_types
            num_scores = len(subset['avg_scores'])
            # 如果用户没有明确指定 score_types，则使用默认格式
            if args.score_types == ['score0', 'score1', 'score2']:
                used_score_types = [f'score{i}' for i in range(num_scores)]
            else:
                used_score_types = args.score_types
                # 检查长度是否匹配
                if len(used_score_types) != num_scores:
                    print(f'Warning: score_types length ({len(used_score_types)}) does not match avg_scores length ({num_scores}) for {subset["name"]}')
                    used_score_types = [f'score{i}' for i in range(num_scores)]
            num_cases = generate_csv_file(csv_path, subset, args.case_range, used_score_types, args.binary_scores)
            print(f'Generated {csv_path} with {num_cases} cases')

        output_info_path = os.path.join(args.output_dir, 'info.json')
        with open(output_info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=4, ensure_ascii=False)

        print(f'Generated {output_info_path}')
    else:
        info = generate_info(args.num_subsets, args.max_dimension, args.max_avg, len(args.score_types))

        for subset in info:
            csv_path = os.path.join(args.output_dir, f'{subset["name"]}.csv')
            num_cases = generate_csv_file(csv_path, subset, args.case_range, args.score_types, args.binary_scores)
            subset['count'] = num_cases
            print(f'Generated {csv_path} with {num_cases} cases')

        info_path = os.path.join(args.output_dir, 'info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=4, ensure_ascii=False)

        print(f'Generated {info_path}')


if __name__ == '__main__':
    main()
