from pathlib import Path
import json
import argparse


def process_jsonl_files(input_dir: str, output_dir: str, default_difficulty: str = "unknown") -> None:
    """
    Process all jsonl files in input directory and save results to output directory.

    Parameters:
    - input_dir: Directory containing jsonl files to process
    - output_dir: Directory to save processed jsonl files
    - default_difficulty: Default value for difficulty field if not present
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory if it doesn't exist
    output_path.mkdir(exist_ok=True, parents=True)

    # Find all jsonl files in input directory (including subdirectories)
    jsonl_files = list(input_path.rglob("*.jsonl"))

    if not jsonl_files:
        print(f"No jsonl files found in {input_dir}")
        return

    print(f"Found {len(jsonl_files)} jsonl files to process")

    for jsonl_path in jsonl_files:
        print(f"\nProcessing: {jsonl_path}")

        # Read and process the jsonl file
        question_data = {}

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Extract required fields from payload
                    payload = data.get("payload", {})
                    question_id = payload.get("_internal_question_id_raw_")
                    if question_id is None:
                        print(f"  Warning: Line {line_num} missing '_internal_question_id_raw_' in payload, skipping")
                        continue

                    avg_score = payload.get("avg_score")
                    if avg_score is None:
                        print(f"  Warning: Line {line_num} missing 'avg_score' in payload, skipping")
                        continue

                    # Extract difficulty or use default
                    difficulty = data.get("difficulty", default_difficulty)

                    # Store data
                    if question_id not in question_data:
                        question_data[question_id] = {
                            "scores": [avg_score],
                            "difficulty": difficulty
                        }
                    else:
                        question_data[question_id]["scores"].append(avg_score)

                except json.JSONDecodeError as e:
                    print(f"  Warning: Line {line_num} invalid JSON: {e}, skipping")
                except Exception as e:
                    print(f"  Warning: Line {line_num} error: {e}, skipping")

        if not question_data:
            print(f"  No valid data found in {jsonl_path.name}")
            continue

        # Calculate average scores and prepare output
        output_data = []
        for qid, data in question_data.items():
            avg_score = sum(data["scores"]) / len(data["scores"])
            output_data.append({
                "id": qid,
                "score": avg_score,
                "difficulty": data["difficulty"]
            })

        # Preserve directory structure
        rel_path = jsonl_path.relative_to(input_path)
        output_file_path = output_path / rel_path
        output_file_path.parent.mkdir(exist_ok=True, parents=True)

        # Write processed data
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for item in output_data:
                json.dump(item, f)
                f.write('\n')

        print(f"  Saved to {output_file_path}")
        print(f"  Processed {len(output_data)} unique entries (from {sum(len(v['scores']) for v in question_data.values())} total lines)")


def main():
    parser = argparse.ArgumentParser(
        description='Process jsonl files: extract questionId, avg_score, difficulty and merge duplicates'
    )
    parser.add_argument(
        '--input', '-i', type=str, required=True,
        help='Directory containing jsonl files to process'
    )
    parser.add_argument(
        '--output', '-o', type=str, required=True,
        help='Directory to save processed jsonl files'
    )
    parser.add_argument(
        '--default-difficulty', '-d', type=str, default='unknown',
        help='Default difficulty value if not present (default: unknown)'
    )
    args = parser.parse_args()

    process_jsonl_files(args.input, args.output, args.default_difficulty)


if __name__ == "__main__":
    main()
