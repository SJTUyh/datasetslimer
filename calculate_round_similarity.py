from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置字体以支持中文显示
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False


def calculate_column_similarity(df):
    """计算DataFrame中数值列之间的相似性（皮尔逊相关系数）"""
    # 获取分数列（排除id和difficulty）
    columns = df.columns.tolist()
    id_idx = columns.index('id')
    difficulty_idx = columns.index('difficulty')
    score_cols = columns[id_idx + 1:difficulty_idx]

    # 计算相关系数矩阵
    correlation_matrix = df[score_cols].corr()

    # 将结果转换为JSON格式
    similarity_result = {}
    for i, col1 in enumerate(score_cols):
        similarity_result[col1] = {}
        for j, col2 in enumerate(score_cols):
            similarity_result[col1][col2] = float(correlation_matrix.iloc[i, j])

    # 计算综合相似性：取上三角部分（不包括对角线）的平均值
    upper_triangle = correlation_matrix.values[np.triu_indices(correlation_matrix.shape[0], k=1)]
    overall_similarity = float(np.mean(upper_triangle)) if len(upper_triangle) > 0 else 0.0

    return similarity_result, overall_similarity


def plot_overall_similarities(subset_names, similarities, output_path):
    """绘制综合相似性的柱状图"""
    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(subset_names, similarities, color='skyblue', edgecolor='navy')

    # 在柱状图上添加具体数值
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f'{height:.4f}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Overall Similarity', fontsize=12)
    ax.set_xlabel('Subset Name', fontsize=12)
    ax.set_title('Overall Similarity of Test Rounds Across Subsets', fontsize=14, fontweight='bold')
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"图表已保存到: {output_path}")


def main(input_dir: str, output_file: str = None):
    input_path = Path(input_dir)

    # 如果没有指定输出文件，默认保存在输入文件夹下
    if output_file is None:
        output_path = input_path / "test_round_similarity.json"
        plot_output_path = input_path / "overall_similarity_plot.png"
    else:
        output_path = Path(output_file)
        plot_output_path = output_path.parent / "overall_similarity_plot.png"

    # 查找所有CSV文件
    csv_files = sorted([f for f in input_path.glob("*.csv")])

    if not csv_files:
        print("没有找到CSV文件")
        return

    print(f"找到 {len(csv_files)} 个CSV文件")

    all_results = {}
    subset_names = []
    overall_similarities = []

    for csv_file in csv_files:
        print(f"\n处理文件: {csv_file.name}")

        try:
            df = pd.read_csv(csv_file)
            print(f"  数据形状: {df.shape}")
            print(f"  列: {list(df.columns)}")

            similarity, overall_sim = calculate_column_similarity(df)
            result = {
                "similarity_matrix": similarity,
                "overall_similarity": overall_sim
            }
            all_results[csv_file.stem] = result

            subset_names.append(csv_file.stem)
            overall_similarities.append(overall_sim)

            print(f"  综合相似性: {overall_sim:.4f}")

        except Exception as e:
            print(f"  处理文件出错: {e}")
            all_results[csv_file.stem] = {"error": str(e)}

    # 保存JSON结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)

    print(f"\nJSON结果已保存到: {output_path}")

    # 绘制并保存图表
    if subset_names:
        plot_overall_similarities(subset_names, overall_similarities, plot_output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="计算测试轮次之间的相似性")
    parser.add_argument("--input", "-i", type=str, default="multi_data_sample",
                        help="包含CSV文件的目录")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="输出JSON文件路径（默认保存在输入文件夹下）")

    args = parser.parse_args()
    main(args.input, args.output)
