from pathlib import Path
import json
import csv
import argparse


def filter_jsonl_by_csv(compressed_dir: str, raw_data_dir: str, output_dir: str) -> None:
    """
    Filter jsonl files based on csv ids from compressed data.

    Parameters:
    - compressed_dir: Directory containing compressed data (folder 1)
    - raw_data_dir: Directory containing raw jsonl data (folder 2)
    - output_dir: Directory to save filtered jsonl files (folder 3)
    """
    compressed_path = Path(compressed_dir)
    raw_data_path = Path(raw_data_dir)
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(exist_ok=True, parents=True)

    # Get representative directory
    representative_dir = compressed_path / "representative"
    if not representative_dir.exists():
        print(f"Error: Representative directory not found at {representative_dir}")
        return

    # Find all csv files in representative directory
    csv_files = list(representative_dir.glob("*.csv"))

    if not csv_files:
        print(f"No csv files found in {representative_dir}")
        return

    print(f"Found {len(csv_files)} csv files to process")

    for csv_path in csv_files:
        print(f"\nProcessing: {csv_path.name}")

        # Read ids from csv
        ids_set = set()
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "id" in row:
                    ids_set.add(row["id"])

        if not ids_set:
            print(f"  No ids found in {csv_path.name}")
            continue

        print(f"{ids_set=}")

        print(f"  Found {len(ids_set)} unique ids")

        # Find corresponding jsonl file in raw data directory
        base_name = csv_path.stem
        jsonl_files = list(raw_data_path.glob(f"{base_name}.jsonl"))

        # Also search recursively if not found at top level
        if not jsonl_files:
            jsonl_files = list(raw_data_path.rglob(f"{base_name}.jsonl"))

        if not jsonl_files:
            print(f"  Warning: No jsonl file found for {base_name}")
            continue

        # Process the first matching jsonl file
        jsonl_path = jsonl_files[0]
        print(f"  Reading from: {jsonl_path}")

        # Filter jsonl
        filtered_lines = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    # Check _internal_question_id_ at top level
                    question_id = data.get("_internal_question_id_")
                    if question_id and question_id in ids_set:
                        filtered_lines.append(line)
                except json.JSONDecodeError as e:
                    print(f"  Warning: Line {line_num} invalid JSON: {e}, skipping")
                except Exception as e:
                    print(f"  Warning: Line {line_num} error: {e}, skipping")

        # Save filtered jsonl
        output_jsonl_path = output_path / f"{base_name}.jsonl"
        with open(output_jsonl_path, 'w', encoding='utf-8') as f:
            for line in filtered_lines:
                f.write(line)
                f.write('\n')

        print(f"  Saved to {output_jsonl_path}")
        print(f"  Filtered {len(filtered_lines)} lines")


def main():
    parser = argparse.ArgumentParser(
        description='Filter jsonl files based on csv ids from compressed data'
    )
    parser.add_argument(
        '--compressed', '-c', type=str, required=True,
        help='Directory containing compressed data (folder 1)'
    )
    parser.add_argument(
        '--raw', '-r', type=str, required=True,
        help='Directory containing raw jsonl data (folder 2)'
    )
    parser.add_argument(
        '--output', '-o', type=str, required=True,
        help='Directory to save filtered jsonl files (folder 3)'
    )
    args = parser.parse_args()

    filter_jsonl_by_csv(args.compressed, args.raw, args.output)


if __name__ == "__main__":
    main()
