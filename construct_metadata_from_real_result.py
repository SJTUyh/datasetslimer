from pathlib import Path
import json
import pandas as pd
import argparse


def read_jsonl(file_path: Path) -> list[dict]:
    """
    Read a jsonl file and return a list of dictionaries.

    Parameters:
    - file_path: Path to the jsonl file

    Returns:
    - List of dictionaries representing each case
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def construct_metadata(input_dir: str, output_dir: str) -> None:
    """
    Construct metadata from multiple test results.

    Parameters:
    - input_dir: Directory containing test results
    - output_dir: Directory to save output metadata files
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory if it doesn't exist
    output_path.mkdir(exist_ok=True, parents=True)

    # Step 1: Find all test directories (e.g., test_0, test_1, ...)
    test_dirs = sorted([d for d in input_path.iterdir() if d.is_dir()])
    num_rounds = len(test_dirs)
    test_dir_names = [d.name for d in test_dirs]
    print(f"Found {num_rounds} test rounds: {test_dir_names}")

    if num_rounds == 0:
        print("Error: No test directories found!")
        return

    # Step 2: Find all subset names from the first test round
    first_test_dir = test_dirs[0]
    subset_files = sorted([f for f in first_test_dir.iterdir() if f.suffix == '.jsonl'])
    subset_names = [f.stem for f in subset_files]
    print(f"Found {len(subset_names)} subsets: {subset_names}")

    if len(subset_names) == 0:
        print("Error: No subset jsonl files found!")
        return

    # Step 3: Process each subset
    info_list = []

    for subset_name in subset_names:
        print(f"\nProcessing subset: {subset_name}")

        # Collect data from all rounds for this subset
        all_rounds_data = []
        for round_idx, test_dir in enumerate(test_dirs):
            jsonl_path = test_dir / f"{subset_name}.jsonl"
            if jsonl_path.exists():
                round_data = read_jsonl(jsonl_path)
                all_rounds_data.append(round_data)
                print(f"  Round {round_idx}: {len(round_data)} cases")
            else:
                print(f"  Warning: Round {round_idx} missing file {subset_name}.jsonl")
                all_rounds_data.append([])

        # Check if we have data from at least one round
        has_data = any(len(data) > 0 for data in all_rounds_data)
        if not has_data:
            print(f"  Skipping subset {subset_name}: no data found")
            continue

        # Step 4: Collect all unique case ids and build case data
        case_data = {}
        difficulty_map = {}

        # First pass: collect all ids and difficulty information
        for round_data in all_rounds_data:
            for case in round_data:
                case_id = case["id"]
                difficulty = case["difficulty"]
                if case_id not in case_data:
                    case_data[case_id] = {
                        "id": case_id,
                        "difficulty": difficulty,
                        "scores": []
                    }
                # Update difficulty map
                if difficulty not in difficulty_map:
                    # Assign numeric value based on existing map size
                    difficulty_map[difficulty] = len(difficulty_map)

        # Second pass: fill in scores from each round
        for round_data in all_rounds_data:
            # Create a map from id to score for this round
            id_to_score = {case["id"]: case["score"] for case in round_data}
            # Fill in scores for each case
            for case_id in case_data:
                case_data[case_id]["scores"].append(id_to_score.get(case_id, 0.0))

        # Step 5: Create DataFrame
        df_data = []
        for case_id, case_info in case_data.items():
            row = {"id": case_id, "difficulty": case_info["difficulty"]}
            for i, score in enumerate(case_info["scores"]):
                row[test_dir_names[i]] = score
            df_data.append(row)

        df = pd.DataFrame(df_data)

        # Reorder columns: id first, then test directory names, then difficulty
        score_cols = test_dir_names
        cols = ["id"] + score_cols + ["difficulty"]
        df = df[cols]

        # Step 6: Save CSV file
        csv_name = f"{subset_name}.csv"
        csv_path = output_path / csv_name
        df.to_csv(csv_path, index=False)
        print(f"  Saved to {csv_path} with {len(df)} cases")

        # Step 7: Calculate avg_scores
        avg_scores = df[score_cols].mean().tolist()

        # Step 8: Add to info list
        info_item = {
            "name": subset_name,
            "count": len(df),
            "avg_scores": avg_scores,
            "difficulty_map": difficulty_map
        }
        info_list.append(info_item)

    # Step 9: Save info.json
    info_path = output_path / "info.json"
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info_list, f, indent=4)
    print(f"\nSaved info.json to {info_path}")

    print(f"\nConstruction complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Construct metadata from multiple real test results'
    )
    parser.add_argument(
        '--input', '-i', type=str, required=True,
        help='Directory containing test results (e.g., ./real_results)'
    )
    parser.add_argument(
        '--output', '-o', type=str, required=True,
        help='Directory to save output metadata files'
    )
    args = parser.parse_args()

    construct_metadata(args.input, args.output)


if __name__ == "__main__":
    main()
