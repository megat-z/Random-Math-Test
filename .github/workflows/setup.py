import json
import os
import logging
from typing import Dict, List, Any
from functools import lru_cache

# Optional: Use rapidfuzz for faster string distance if desired, fallback to pure Python
try:
    from rapidfuzz.distance import Levenshtein
    def levenshtein_distance(s1, s2):
        return Levenshtein.distance(s1, s2)
except ImportError:
    def levenshtein_distance(s1, s2):
        """Fast Levenshtein distance for two strings."""
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        if not s2:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
            prev = curr
        return prev[-1]

@lru_cache(maxsize=4096)
def normalized_levenshtein(s1: str, s2: str) -> float:
    if not s1 and not s2:
        return 0.0
    maxlen = max(len(s1), len(s2))
    if maxlen == 0:
        return 0.0
    return levenshtein_distance(s1, s2) / maxlen

def min_normalized_levenshtein(vals1: List[Any], vals2: List[Any]) -> float:
    """Compute minimum normalized Levenshtein distance between two lists of values."""
    dists = [
        normalized_levenshtein(str(v1), str(v2))
        for v1 in vals1 for v2 in vals2
    ]
    return min(dists) if dists else 0.0

def compute_matrix(ids: List[str], values_dict: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Compute normalized Levenshtein distance between all pairs in ids, using values_dict.
    Returns: dict[id][id] = min normalized distance.
    """
    matrix = {id1: {} for id1 in ids}
    for idx1, id1 in enumerate(ids):
        vals1 = values_dict.get(id1, [])
        vals1 = vals1 if isinstance(vals1, list) else [vals1]
        matrix[id1][id1] = 0.0
        for idx2 in range(idx1 + 1, len(ids)):
            id2 = ids[idx2]
            vals2 = values_dict.get(id2, [])
            vals2 = vals2 if isinstance(vals2, list) else [vals2]
            dist = min_normalized_levenshtein(vals1, vals2)
            matrix[id1][id2] = dist
            matrix[id2][id1] = dist
    return matrix

def check_test_script_exists(case: Dict[str, Any], scripts_dir: str, case_id: str) -> bool:
    """Checks if a script is defined in the test case or exists by convention in directory."""
    script_name = case.get("script")
    if script_name:
        script_path = os.path.join(scripts_dir, script_name)
    else:
        # Try convention: <case_id>.py in test-scripts
        script_path = os.path.join(scripts_dir, f"{case_id}.py")
    return os.path.isfile(script_path)

def log_missing_scripts(test_cases: Dict[str, Any], scripts_dir: str) -> List[str]:
    missing = []
    for case_id, case in test_cases.items():
        if not check_test_script_exists(case, scripts_dir, case_id):
            missing.append(case_id)
    return missing

def main():
    test_case_file = os.path.join("test", "test-cases.json")
    string_distance_dir = os.path.join("test", "string-distances")
    input_matrix_file = os.path.join(string_distance_dir, "input.json")
    output_matrix_file = os.path.join(string_distance_dir, "output.json")
    scripts_dir = os.path.join("test", "test-scripts")

    os.makedirs(string_distance_dir, exist_ok=True)

    # Logging setup
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    # Load test cases
    try:
        with open(test_case_file, "r") as f:
            test_cases = json.load(f)
        if not isinstance(test_cases, dict) or not test_cases:
            logging.error("No test cases found. Exiting.")
            return
    except Exception as e:
        logging.error(f"Error loading {test_case_file}: {e}")
        return

    ids = list(test_cases.keys())
    input_values = {tid: test_cases[tid].get("input", "") for tid in ids}
    output_values = {tid: test_cases[tid].get("output", "") for tid in ids if "output" in test_cases[tid] and test_cases[tid]["output"] not in ("", None)}
    has_output = bool(output_values)

    logging.info(f"Calculating input distance matrix for {len(ids)} cases...")
    input_matrix = compute_matrix(ids, input_values)
    with open(input_matrix_file, "w") as f:
        json.dump(input_matrix, f, indent=2)

    if has_output:
        logging.info(f"Calculating output distance matrix for {len(ids)} cases...")
        output_matrix = compute_matrix(ids, output_values)
        with open(output_matrix_file, "w") as f:
            json.dump(output_matrix, f, indent=2)
    else:
        logging.info("No valid outputs found. Skipping output distance matrix.")

    # Check for missing scripts
    missing_scripts = log_missing_scripts(test_cases, scripts_dir)
    if missing_scripts:
        logging.warning(f"Missing test scripts for cases: {', '.join(missing_scripts)}")
        print(f"WARNING: Missing test scripts for cases: {', '.join(missing_scripts)}")
    else:
        logging.info("All test cases have corresponding scripts.")

    logging.info(f"Successfully created distance matrices for {len(ids)} cases.")

if __name__ == "__main__":
    main()