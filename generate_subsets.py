from pathlib import Path
import json
import argparse
import pandas as pd
import numpy as np
import warnings
from sklearn.cluster import KMeans
from sklearn.utils import resample

def prepare_data(data: pd.DataFrame, difficulty_map: dict = None) -> pd.DataFrame:
    """
    Prepare data by mapping difficulty and creating numeric version.

    Parameters:
    - data: Raw DataFrame with original columns
    - difficulty_map: Custom mapping from difficulty strings to numeric values

    Returns:
    - Processed numeric DataFrame
    """
    if difficulty_map is None:
        difficulty_map = {
            'level0': 0,
            'level1': 1,
            'level2': 2
        }
    data = data.copy()
    data["difficulty"] = data["difficulty"].map(difficulty_map)

    # Create numeric version for clustering - drop id column
    data_numeric = data.drop(columns=["id"])
    data_numeric = data_numeric.fillna(0)

    return data_numeric

def compute_kmeans(data: pd.DataFrame, n_clusters: int, random_state: int = 42) -> tuple:
    """
    Compute k-means clustering on the given data.

    Parameters:
    - data: DataFrame containing the data to cluster
    - n_clusters: Number of clusters to form

    Returns:
    - Cluster labels and centers
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Number of distinct clusters.*found smaller than n_clusters.*')
        kmeans.fit(data)
    return kmeans.labels_, kmeans.cluster_centers_

def draw_representative_sample(data: pd.DataFrame, labels: np.ndarray, n: int, random_state: int = 1, difficulty_map: dict = None) -> pd.DataFrame:
    """
    Draw N representative datapoints based on k-means clustering labels.
    First selects the point closest to each cluster centroid,
    then distributes remaining samples proportionally.

    Parameters:
    - data: DataFrame containing the data to sample from
    - labels: Cluster labels for each data point
    - n: Number of representative datapoints to draw
    - random_state: Random seed for reproducibility
    - difficulty_map: Custom mapping from difficulty strings to numeric values

    Returns:
    - DataFrame containing the representative sample
    """
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    # Ensure n is not larger than data size
    n = min(n, len(data))

    # If n is less than number of clusters, adjust n_clusters
    if n < n_clusters:
        n_clusters = n

    # First, get the point closest to centroid for each cluster
    data_numeric = prepare_data(data, difficulty_map)
    centroid_samples = pd.DataFrame()
    remaining_data = data.copy()
    remaining_indices = np.ones(len(data), dtype=bool)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Number of distinct clusters.*found smaller than n_clusters.*')
        kmeans.fit(data_numeric)
    centroids = kmeans.cluster_centers_

    # Select points closest to centroids
    for label, centroid in zip(unique_labels[:n_clusters], centroids):
        cluster_mask = labels == label
        cluster_data_numeric = data_numeric[cluster_mask]

        # Calculate distances to centroid
        distances = np.linalg.norm(cluster_data_numeric - centroid, axis=1)
        closest_idx = np.argmin(distances)

        # Get the original index in the full dataset
        original_idx = np.where(cluster_mask)[0][closest_idx]

        # Add to centroid samples and mark for removal from remaining data
        centroid_samples = pd.concat([centroid_samples, data.iloc[[original_idx]]])
        remaining_indices[original_idx] = False

    # Update remaining data
    remaining_data = data[remaining_indices]
    remaining_labels = labels[remaining_indices]

    # Calculate proportional distribution for remaining samples
    remaining_n = n - n_clusters
    if remaining_n > 0 and len(remaining_data) > 0:
        # Count remaining points per cluster
        unique_remaining_labels, counts = np.unique(remaining_labels, return_counts=True)
        proportions = counts / counts.sum()

        # Calculate samples per cluster
        exact_samples = proportions * remaining_n
        sample_counts = exact_samples.astype(int)
        fractions = exact_samples - sample_counts

        # Distribute remaining samples based on largest fractional parts
        remaining = remaining_n - sample_counts.sum()
        if remaining > 0:
            fraction_indices = np.argsort(fractions)[-remaining:]
            for idx in fraction_indices:
                sample_counts[idx] += 1

        # Sample from remaining points
        additional_samples = pd.DataFrame()
        for label, count in zip(unique_remaining_labels, sample_counts):
            if count > 0:
                cluster_data = remaining_data[remaining_labels == label]
                count = min(count, len(cluster_data))
                if count > 0:
                    cluster_sample = resample(cluster_data,
                                           n_samples=count,
                                           random_state=random_state,
                                           replace=False)
                    additional_samples = pd.concat([additional_samples, cluster_sample])

        # Combine centroid samples with additional samples
        representative_sample = pd.concat([centroid_samples, additional_samples])
    else:
        representative_sample = centroid_samples

    return representative_sample

def get_random_sample(data: pd.DataFrame, sample_size: int, random_state: int = 1) -> pd.DataFrame:
    """
    Get a random sample from the dataset.

    Parameters:
    - data: DataFrame to sample from
    - sample_size: Number of samples to draw

    Returns:
    - Random sample DataFrame
    """
    sample_size = min(sample_size, len(data))
    return data.sample(n=sample_size, random_state=random_state)

def save_sample_and_ids(sample: pd.DataFrame, name: str, data_dir: Path) -> None:
    """
    Save a sample DataFrame and its IDs to files.

    Parameters:
    - sample: DataFrame to save
    - name: Name prefix for the files
    - data_dir: Directory to save the files
    """
    # Save full sample
    sample.to_csv(data_dir / f"{name}.csv", index=False)

    # Save IDs
    with open(data_dir / f"{name}_ids.json", 'w') as f:
        json.dump(sample["id"].tolist(), f)

def calculate_optimal_parameters(data: pd.DataFrame, data_size: int, compression_ratio: float = 0.1) -> tuple:
    """
    Calculate optimal n_clusters and n_samples based on data size and compression ratio.
    Also ensures n_clusters doesn't exceed the number of unique data combinations.

    Parameters:
    - data: DataFrame to check for unique data combinations
    - data_size: Total number of samples in dataset
    - compression_ratio: Target compression ratio (0-1)

    Returns:
    - Tuple of (n_clusters, n_samples)
    """
    n_samples = max(int(data_size * compression_ratio), 10)
    n_samples = min(n_samples, data_size)

    # Calculate number of unique data combinations (excluding id column)
    if 'id' in data.columns:
        unique_data = data.drop(columns=['id']).drop_duplicates()
    else:
        unique_data = data.drop_duplicates()
    n_unique = len(unique_data)

    # Calculate initial n_clusters
    initial_n_clusters = min(int(np.sqrt(n_samples)), n_samples)
    # Ensure n_clusters doesn't exceed the number of unique data combinations
    n_clusters = min(initial_n_clusters, n_unique)
    n_clusters = max(n_clusters, 2)

    # Print warning if clusters were adjusted
    if initial_n_clusters > n_unique:
        print(f"  Warning: Only {n_unique} unique data combinations found, adjusted n_clusters from {initial_n_clusters} to {n_clusters}")

    return n_clusters, n_samples

def process_single_dataset(info_item: dict, input_dir: Path, repr_dir: Path, random_dir: Path, compression_ratio: float, random_state: int = 42) -> tuple:
    """
    Process a single dataset from the info.json.

    Parameters:
    - info_item: Dictionary with dataset information from info.json
    - input_dir: Directory containing input metadata files
    - repr_dir: Directory to save representative samples
    - random_dir: Directory to save random samples
    - compression_ratio: Target compression ratio
    - random_state: Random seed

    Returns:
    - Tuple of (repr_info, rand_info)
    """
    dataset_name = info_item["name"]
    difficulty_map = info_item["difficulty_map"]

    # Load data
    csv_path = input_dir / f"{dataset_name}.csv"
    data = pd.read_csv(csv_path)
    data_size = len(data)
    print(f"  Loaded {dataset_name} with {data_size} samples")

    # Calculate optimal parameters
    n_clusters, n_samples = calculate_optimal_parameters(data, data_size, compression_ratio)
    print(f"  Optimal parameters: n_clusters={n_clusters}, n_samples={n_samples}")

    # Prepare data
    data_numeric = prepare_data(data, difficulty_map)

    # Generate clusters
    labels, _ = compute_kmeans(data_numeric, n_clusters, random_state)

    # Generate samples
    representative_sample = draw_representative_sample(data, labels, n_samples, random_state, difficulty_map)
    random_sample = get_random_sample(data, n_samples, random_state)

    # Create directories
    repr_dir.mkdir(exist_ok=True, parents=True)
    random_dir.mkdir(exist_ok=True, parents=True)

    # Save representative sample
    save_sample_and_ids(representative_sample, dataset_name, repr_dir)

    # Save random sample
    save_sample_and_ids(random_sample, dataset_name, random_dir)

    # Calculate avg_scores
    score_cols = [col for col in data.columns if col.startswith("score")]

    # Create updated info items
    repr_info = {
        "name": dataset_name,
        "count": len(representative_sample),
        "avg_scores": representative_sample[score_cols].mean().tolist(),
        "difficulty_map": difficulty_map
    }

    rand_info = {
        "name": dataset_name,
        "count": len(random_sample),
        "avg_scores": random_sample[score_cols].mean().tolist(),
        "difficulty_map": difficulty_map
    }

    return repr_info, rand_info

def main(input_dir: str,
         output_dir: str,
         compression_ratio: float = 0.1,
         random_state: int = 42) -> None:
    """
    Generate and save different samples from multiple datasets.

    Parameters:
    - input_dir: Directory containing info.json and metadata CSV files
    - output_dir: Directory to save output samples
    - compression_ratio: Target compression ratio (0-1)
    - random_state: Random seed for reproducibility
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create subdirectories for different sampling methods
    repr_output_dir = output_path / "representative"
    random_output_dir = output_path / "random"

    # Load info.json
    info_path = input_path / "info.json"
    with open(info_path, 'r', encoding='utf-8') as f:
        original_info = json.load(f)

    print(f"Loaded info.json with {len(original_info)} datasets")

    # Process each dataset
    repr_info_list = []
    rand_info_list = []

    for info_item in original_info:
        print(f"\nProcessing {info_item['name']}...")
        repr_info, rand_info = process_single_dataset(
            info_item, input_path, repr_output_dir, random_output_dir, compression_ratio, random_state
        )
        repr_info_list.append(repr_info)
        rand_info_list.append(rand_info)

    # Save info.json for representative samples
    with open(repr_output_dir / "info.json", 'w', encoding='utf-8') as f:
        json.dump(repr_info_list, f, indent=4)

    # Save info.json for random samples
    with open(random_output_dir / "info.json", 'w', encoding='utf-8') as f:
        json.dump(rand_info_list, f, indent=4)

    print(f"\nCompression complete!")
    print(f"  - Representative samples saved to: {repr_output_dir}")
    print(f"  - Random samples saved to: {random_output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate representative dataset subsets using k-means clustering')
    parser.add_argument('--input', '-i', type=str, required=True,
                        help='Directory containing info.json and metadata CSV files')
    parser.add_argument('--output', '-o', type=str, required=True,
                        help='Directory to save output samples')
    parser.add_argument('--compression-ratio', '-r', type=float, default=0.1,
                        help='Target compression ratio (0-1, default: 0.1)')
    parser.add_argument('--random-state', '-s', type=int, default=42,
                        help='Random seed for reproducibility (default: 42)')

    args = parser.parse_args()

    main(
        input_dir=args.input,
        output_dir=args.output,
        compression_ratio=args.compression_ratio,
        random_state=args.random_state
    )