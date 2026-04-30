from pathlib import Path
import json
import argparse
import pandas as pd
import numpy as np
import warnings
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def prepare_numeric_data(data: pd.DataFrame, replace_difficulty_with_number: bool = False,
                         difficulty_map: dict = None) -> pd.DataFrame:
    """Prepare numeric data for analysis by removing non-numeric columns and filling NaNs."""
    data = data.copy()
    if replace_difficulty_with_number:
        if 'difficulty' in data.columns:
            if difficulty_map is None:
                difficulty_map = {
                    'level0': 0,
                    'level1': 1,
                    'level2': 2
                }
            # 确保difficulty值是字符串类型
            data["difficulty"] = data["difficulty"].astype(str)
            # 打印转换前的困难度值
            print(f"Difficulty values before mapping: {data['difficulty'].unique()}")
            # 映射困难度值
            data["difficulty"] = data["difficulty"].map(difficulty_map)
            # 打印转换后的困难度值
            print(f"Difficulty values after mapping: {data['difficulty'].unique()}")
        else:
            print("Warning: No difficulty column found for mapping")

    # Drop id column if exists, keep others
    drop_cols = []
    if 'id' in data.columns:
        drop_cols.append('id')
    if 'environment' in data.columns:
        drop_cols.append('environment')
    if 'size_in_gb' in data.columns:
        drop_cols.append('size_in_gb')

    return data.drop(columns=drop_cols, errors='ignore').fillna(0)

def compare_means_single(dataset_name: str, full_data: pd.DataFrame, representative: pd.DataFrame,
                         random: pd.DataFrame, figures_path: Path) -> pd.DataFrame:
    """
    Compare means of different samples against full dataset for a single dataset.
    """
    # Find score columns (between id and difficulty)
    full_cols = full_data.columns.tolist()
    id_idx = full_cols.index('id')
    difficulty_idx = full_cols.index('difficulty')
    score_cols = full_cols[id_idx + 1:difficulty_idx]

    # Calculate means
    means_df = pd.DataFrame({
        "Full Dataset": full_data.mean(numeric_only=True),
        "K-means Representative": representative.mean(numeric_only=True),
        "Random": random.mean(numeric_only=True)
    })

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    bar_width = 0.25
    r = np.arange(len(score_cols))

    # Add grid
    ax.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)

    for idx, (sample_name, means) in enumerate(means_df.items()):
        position = r + idx * bar_width
        bars = ax.bar(position, means[score_cols], bar_width, label=sample_name, zorder=3)

        # Add value labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9, rotation=0)

    ax.set_ylabel('Mean Value')
    ax.set_title(f'Means Comparison - {dataset_name}')
    ax.set_xticks(r + bar_width)
    ax.set_xticklabels(score_cols, rotation=45, ha='right')
    ax.legend()

    plt.tight_layout()
    plt.savefig(figures_path / f'{dataset_name}_means_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    return means_df

def compare_difficulty_distributions_single(dataset_name: str, samples: dict,
                                            figures_path: Path) -> pd.DataFrame:
    """Compare and plot difficulty distributions across samples for a single dataset."""
    distributions = {}
    for name, df in samples.items():
        if 'difficulty' in df.columns:
            dist = df['difficulty'].value_counts(normalize=True)
            distributions[name] = dist

    if not distributions:
        return pd.DataFrame()

    # Create a DataFrame from the distributions dictionary
    dist_df = pd.DataFrame(distributions).fillna(0)

    # Plot the distributions
    fig, ax = plt.subplots(figsize=(10, 5))
    dist_df.plot(kind='bar', ax=ax)

    # Add value labels on top of each bar
    for container in ax.containers:
        ax.bar_label(container, fmt='%.3f', padding=3, fontsize=9)

    # Add grid
    ax.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)
    ax.set_axisbelow(True)

    plt.title(f'Difficulty Distributions - {dataset_name}')
    plt.xlabel('Difficulty')
    plt.ylabel('Proportion')
    plt.legend(title='Sample')
    plt.tight_layout()

    plt.savefig(figures_path / f'{dataset_name}_difficulty_distributions.png', dpi=300, bbox_inches='tight')
    plt.close()

    return dist_df

def compare_correlation_patterns(full_data: pd.DataFrame, subset_data: pd.DataFrame) -> tuple:
    """Compare correlation patterns between full dataset and subset."""
    if len(full_data.columns) < 2 or len(subset_data.columns) < 2:
        return np.nan, np.nan

    try:
        full_corr = np.corrcoef(full_data.T)
        subset_corr = np.corrcoef(subset_data.T)

        # Get upper triangular values (excluding diagonal)
        full_corr_vals = full_corr[np.triu_indices(full_corr.shape[0], k=1)]
        subset_corr_vals = subset_corr[np.triu_indices(subset_corr.shape[0], k=1)]

        return np.nanmean(full_corr_vals), np.nanmean(subset_corr_vals)
    except:
        return np.nan, np.nan

def process_single_dataset(dataset_name: str, original_dir: Path, repr_dir: Path,
                          random_dir: Path, figures_path: Path,
                          difficulty_map: dict = None) -> dict:
    """Process and compare a single dataset."""
    print(f"\n=== Processing {dataset_name} ===")

    try:
        # Load datasets
        full_data = pd.read_csv(original_dir / f"{dataset_name}.csv")
        representative = pd.read_csv(repr_dir / f"{dataset_name}.csv")
        random_sample = pd.read_csv(random_dir / f"{dataset_name}.csv")

        print(f"Original dataset size: {len(full_data)}")
        print(f"Representative sample size: {len(representative)}")
        print(f"Random sample size: {len(random_sample)}")

        # 确保difficulty字段存在且格式一致
        for df in [full_data, representative, random_sample]:
            if 'difficulty' in df.columns:
                # 检查difficulty字段类型
                print(f"Difficulty column type: {df['difficulty'].dtype}")
                # 确保所有值都是字符串类型
                df['difficulty'] = df['difficulty'].astype(str)
                # 打印前几个值，方便调试
                print(f"First few difficulty values: {df['difficulty'].head().tolist()}")
            else:
                print("Warning: No difficulty column found")

        # Prepare numeric versions
        full_numeric = prepare_numeric_data(full_data)
        representative_numeric = prepare_numeric_data(representative)
        random_numeric = prepare_numeric_data(random_sample)

        # Compare means - use original data to find column positions
        means_df = compare_means_single(dataset_name, full_data, representative, random_sample, figures_path)

        # Compare difficulty distributions
        samples = {
            "Full Dataset": full_data,
            "Representative Sample": representative,
            "Random Sample": random_sample
        }
        difficulty_dist = compare_difficulty_distributions_single(dataset_name, samples, figures_path)

        # Compare correlation patterns
        results = {
            "dataset_name": dataset_name,
            "sizes": {
                "full": len(full_data),
                "representative": len(representative),
                "random": len(random_sample)
            },
            "means": means_df.to_dict()
        }

        # Try correlation comparison
        full_num_with_diff = prepare_numeric_data(full_data, replace_difficulty_with_number=True, difficulty_map=difficulty_map)
        repr_num_with_diff = prepare_numeric_data(representative, replace_difficulty_with_number=True, difficulty_map=difficulty_map)
        rand_num_with_diff = prepare_numeric_data(random_sample, replace_difficulty_with_number=True, difficulty_map=difficulty_map)

        repr_corr = compare_correlation_patterns(full_num_with_diff, repr_num_with_diff)
        rand_corr = compare_correlation_patterns(full_num_with_diff, rand_num_with_diff)

        results["correlations"] = {
            "representative": {"full": repr_corr[0], "sample": repr_corr[1]},
            "random": {"full": rand_corr[0], "sample": rand_corr[1]}
        }

        return results

    except Exception as e:
        print(f"Error processing {dataset_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main(original_dir: str,
         compressed_dir: str,
         figures_dir: str = "figures") -> None:
    """Compare multiple datasets using various metrics."""
    # Filter out RuntimeWarning about invalid values in divide
    warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')

    # Create figures directory
    figures_path = Path(figures_dir)
    figures_path.mkdir(exist_ok=True, parents=True)

    original_path = Path(original_dir)
    compressed_path = Path(compressed_dir)
    repr_path = compressed_path / "representative"
    random_path = compressed_path / "random"

    # Load info.json from original directory
    with open(original_path / "info.json", 'r', encoding='utf-8') as f:
        original_info = json.load(f)

    print(f"Loaded {len(original_info)} datasets from info.json")

    # Process each dataset
    all_results = []
    for info_item in original_info:
        dataset_name = info_item["name"]
        difficulty_map = info_item.get("difficulty_map", None)

        result = process_single_dataset(
            dataset_name,
            original_path,
            repr_path,
            random_path,
            figures_path,
            difficulty_map
        )

        if result:
            all_results.append(result)

    # Save summary results
    summary_path = figures_path / "comparison_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=4)

    print(f"\n=== Summary ===")
    print(f"Processed {len(all_results)} datasets")
    print(f"All figures saved to: {figures_path}")
    print(f"Summary saved to: {summary_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare original datasets with compressed samples')
    parser.add_argument('--original', '-o', type=str, required=True,
                        help='Directory containing original datasets and info.json')
    parser.add_argument('--compressed', '-c', type=str, required=True,
                        help='Directory containing compressed datasets (with representative and random subdirs)')
    parser.add_argument('--figures-dir', '-f', type=str, default='figures',
                        help='Directory to save figures (default: figures)')

    args = parser.parse_args()

    main(
        original_dir=args.original,
        compressed_dir=args.compressed,
        figures_dir=args.figures_dir
    )
