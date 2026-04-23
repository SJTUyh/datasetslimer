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

    # 删除分数列全是0的行
    original_count = len(df)
    mask = (df[score_cols] == 0).all(axis=1)
    df_clean = df[~mask].copy()
    cleaned_count = len(df_clean)
    removed_count = original_count - cleaned_count

    if cleaned_count == 0:
        print(f"    警告：所有行都被删除（全是0），无法计算相似度")
        similarity_result = {col: {col: 1.0 for col in score_cols} for col in score_cols}
        return similarity_result, 0.0, original_count, cleaned_count, removed_count

    # 计算相关系数矩阵
    correlation_matrix = df_clean[score_cols].corr()

    # 将结果转换为JSON格式
    similarity_result = {}
    for i, col1 in enumerate(score_cols):
        similarity_result[col1] = {}
        for j, col2 in enumerate(score_cols):
            similarity_result[col1][col2] = float(correlation_matrix.iloc[i, j])

    # 计算综合相似性：取上三角部分（不包括对角线）的平均值
    upper_triangle = correlation_matrix.values[np.triu_indices(correlation_matrix.shape[0], k=1)]
    raw_similarity = float(np.mean(upper_triangle)) if len(upper_triangle) > 0 else 0.0

    # 修正综合相似度：使用自由度修正，考虑样本大小
    # 当样本数量较少时，相关系数可能有更大的方差，需要修正
    # 使用 n-1 作为自由度进行修正
    if cleaned_count > 1:
        # 使用 Fisher z 变换，考虑自由度来调整标准误差
        # 这里使用简单但有效的修正：对于小样本，调整幅度
        # 基本思想是：样本数越少，修正幅度越大（向0靠近）
        df_effective = cleaned_count - 2  # 相关系数的自由度
        if df_effective > 0:
            # 使用 t 分布的影响来调整
            # 简单的修正因子：当样本数很少时，更多地向0收缩
            shrinkage_factor = min(1.0, np.sqrt(df_effective / 10))  # 当 df < 10 时逐渐收缩
            corrected_similarity = raw_similarity * shrinkage_factor
        else:
            corrected_similarity = raw_similarity
    else:
        corrected_similarity = raw_similarity

    return similarity_result, raw_similarity, corrected_similarity, original_count, cleaned_count, removed_count


def plot_overall_similarities(subset_names, similarities_raw, similarities_corrected, cleaned_counts, output_path):
    """绘制综合相似性的柱状图"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 第一张图：原始相似度和修正后的相似度对比
    x = np.arange(len(subset_names))
    width = 0.35

    bars1 = axes[0].bar(x - width/2, similarities_raw, width, label='Raw Similarity', color='skyblue', edgecolor='navy')
    bars2 = axes[0].bar(x + width/2, similarities_corrected, width, label='Corrected Similarity', color='lightcoral', edgecolor='darkred')

    # 添加数值
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width() / 2., height,
                        f'{height:.4f}',
                        ha='center', va='bottom', fontsize=10)

    axes[0].set_ylabel('Similarity', fontsize=12)
    axes[0].set_xlabel('Subset Name', fontsize=12)
    axes[0].set_title('Raw vs Corrected Similarity', fontsize=14, fontweight='bold')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(subset_names, rotation=45, ha='right')
    axes[0].legend()
    axes[0].grid(True, axis='y', linestyle='--', alpha=0.7)

    # 第二张图：修正后的相似度和数据量
    ax2 = axes[1].twinx()
    bars3 = axes[1].bar(subset_names, similarities_corrected, color='lightcoral', edgecolor='darkred', label='Corrected Similarity', alpha=0.7)
    line2 = ax2.plot(subset_names, cleaned_counts, 'o-', color='darkgreen', linewidth=2, markersize=8, label='Valid Cases')

    # 添加数值
    for bar in bars3:
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.4f}',
                    ha='center', va='bottom', fontsize=10, color='darkred')

    axes[1].set_ylabel('Corrected Similarity', fontsize=12, color='darkred')
    ax2.set_ylabel('Number of Valid Cases', fontsize=12, color='darkgreen')
    axes[1].set_xlabel('Subset Name', fontsize=12)
    axes[1].set_title('Corrected Similarity with Case Count', fontsize=14, fontweight='bold')
    axes[1].tick_params(axis='y', labelcolor='darkred')
    ax2.tick_params(axis='y', labelcolor='darkgreen')
    axes[1].set_xticks(range(len(subset_names)))
    axes[1].set_xticklabels(subset_names, rotation=45, ha='right')
    axes[1].grid(True, axis='y', linestyle='--', alpha=0.7)

    # 添加图例
    lines1, labels1 = axes[1].get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    axes[1].legend(lines1 + lines2, labels1 + labels2, loc='upper left')

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
    similarities_raw = []
    similarities_corrected = []
    cleaned_counts = []

    for csv_file in csv_files:
        print(f"\n处理文件: {csv_file.name}")

        try:
            df = pd.read_csv(csv_file)
            print(f"  原始数据: {df.shape[0]} 行")
            print(f"  列: {list(df.columns)}")

            similarity, raw_sim, corrected_sim, original_count, cleaned_count, removed_count = calculate_column_similarity(df)

            result = {
                "similarity_matrix": similarity,
                "raw_similarity": raw_sim,
                "corrected_similarity": corrected_sim,
                "original_count": original_count,
                "cleaned_count": cleaned_count,
                "removed_count": removed_count
            }
            all_results[csv_file.stem] = result

            subset_names.append(csv_file.stem)
            similarities_raw.append(raw_sim)
            similarities_corrected.append(corrected_sim)
            cleaned_counts.append(cleaned_count)

            print(f"  原始相似性: {raw_sim:.4f}")
            print(f"  修正后相似性: {corrected_sim:.4f}")
            print(f"  有效数据: {cleaned_count} 行 (删除了 {removed_count} 行全0数据)")

        except Exception as e:
            print(f"  处理文件出错: {e}")
            all_results[csv_file.stem] = {"error": str(e)}

    # 保存JSON结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)

    print(f"\nJSON结果已保存到: {output_path}")

    # 绘制并保存图表
    if subset_names:
        plot_overall_similarities(subset_names, similarities_raw, similarities_corrected, cleaned_counts, plot_output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="计算测试轮次之间的相似性")
    parser.add_argument("--input", "-i", type=str, default="multi_data_sample",
                        help="包含CSV文件的目录")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="输出JSON文件路径（默认保存在输入文件夹下）")

    args = parser.parse_args()
    main(args.input, args.output)
