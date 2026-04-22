from pathlib import Path
import json
import random

def create_test_data():
    """
    Create test data for the construct_from_real_ds.py script.
    """
    base_dir = Path("test_real_results")

    # Create test rounds
    num_rounds = 3
    num_subsets = 2
    cases_per_subset = 10

    # Create case ids and data
    case_ids = [f"case_{i:03d}" for i in range(cases_per_subset)]
    difficulty_levels = ["level0", "level1", "level2"]

    for round_idx in range(num_rounds):
        round_dir = base_dir / f"test_{round_idx}"
        round_dir.mkdir(parents=True, exist_ok=True)

        for subset_idx in range(num_subsets):
            subset_name = f"subset_{subset_idx}"
            jsonl_path = round_dir / f"{subset_name}.jsonl"

            cases = []
            for case_id in case_ids:
                # Random difficulty for each case (consistent across rounds)
                difficulty_seed = int(case_id.split("_")[1]) + subset_idx * 100
                difficulty_idx = difficulty_seed % len(difficulty_levels)

                # Random score for each round
                score = round(random.uniform(0, 1), 2)

                cases.append({
                    "id": case_id,
                    "score": score,
                    "difficulty": difficulty_levels[difficulty_idx]
                })

            # Write jsonl file
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for case in cases:
                    json.dump(case, f)
                    f.write('\n')

    print(f"Created test data in {base_dir}")
    print(f"  {num_rounds} test rounds")
    print(f"  {num_subsets} subsets per round")
    print(f"  {cases_per_subset} cases per subset")

if __name__ == "__main__":
    create_test_data()
