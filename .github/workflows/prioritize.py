import os
import json
import numpy as np
import re
from typing import Dict, List, Tuple

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def check_test_cases(path):
    if not os.path.isfile(path):
        print(f"ERROR: {path} not found.")
        return None
    try:
        cases = load_json(path)
        assert isinstance(cases, dict) and all(
            isinstance(v, dict) and "input" in v and "output" in v
            for v in cases.values()
        )
        return cases
    except Exception as e:
        print(f"ERROR: test-cases.json formatting issue: {e}")
        return None

def load_matrix(path, ids):
    """
    Loads a square matrix dict[id1][id2] -> float into a numpy array aligned to ids.
    If file doesn't exist, returns zeros.
    """
    if not os.path.isfile(path):
        return np.zeros((len(ids), len(ids)), dtype=np.float32)
    m = load_json(path)
    arr = np.zeros((len(ids), len(ids)), dtype=np.float32)
    for i, id1 in enumerate(ids):
        row = m.get(id1, {})
        for j, id2 in enumerate(ids):
            arr[i, j] = float(row.get(id2, 0.0))
    return arr

def list_fault_versions(dir_path) -> List[Tuple[int, str]]:
    if not os.path.isdir(dir_path):
        return []
    out = []
    for f in os.listdir(dir_path):
        m = re.match(r"^V(\d+)\.json$", f)
        if m:
            try:
                out.append((int(m.group(1)), os.path.join(dir_path, f)))
            except ValueError:
                pass
    return sorted(out, key=lambda x: x[0])

def get_reward_from_history(dir_path: str, ids: List[str], decay: float = 0.7) -> np.ndarray:
    """
    Build a reward vector using an EMA over all fault matrices.
    - Each matrix is a per-TCID {id: 0|1}, where 1 indicates failure.
    - decay in [0,1): higher means longer memory; 0.7 favors recent cycles.
    Starts from neutral 0.5 to avoid over-penalizing unseen IDs.
    """
    versions = list_fault_versions(dir_path)
    if not versions:
        return np.zeros(len(ids), dtype=np.float32)

    r = np.full(len(ids), 0.5, dtype=np.float32)
    alpha = 1.0 - decay  # EMA update factor
    for _, path in versions:
        try:
            vmap = load_json(path)
        except Exception:
            continue
        v = np.array([float(vmap.get(tid, 0.0)) for tid in ids], dtype=np.float32)
        r = decay * r + alpha * v
    return r

def prioritize_order(ids, input_mat, output_mat, reward_vec, alpha=0.5, beta=0.5, gamma=1.0):
    """
    Score = alpha * avg_input_distance + beta * avg_output_distance + gamma * reward
    - avg distances are per-row averages in [0,1]
    - reward is from EMA of fault history in [0,1]
    """
    n = len(ids)
    denom = max(n - 1, 1)
    avg_input = np.sum(input_mat, axis=1) / denom
    avg_output = np.sum(output_mat, axis=1) / denom

    # If output_mat was missing (all zeros), keep avg_output at zeros to avoid bias
    if np.allclose(output_mat, 0.0):
        avg_output = np.zeros_like(avg_output)

    scores = alpha * avg_input + beta * avg_output + gamma * reward_vec

    # Stable tie-break by ID to make order deterministic across runs
    stable_indices = np.lexsort((np.array(ids), -scores))
    order = [ids[i] for i in stable_indices[::-1]]
    return order, scores

def main():
    tc_path = "test/test-cases.json"
    input_path = "test/string-distances/input.json"
    output_path = "test/string-distances/output.json"
    fault_dir = "test/fault-matrices"
    tcp_order_path = "test/tcp.json"

    cases = check_test_cases(tc_path)
    if cases is None:
        print("Test case check failed. Exiting.")
        return

    ids = sorted(cases.keys())
    input_mat = load_matrix(input_path, ids)
    output_mat = load_matrix(output_path, ids)
    reward_vec = get_reward_from_history(fault_dir, ids, decay=0.7)

    tcp_order, scores = prioritize_order(ids, input_mat, output_mat, reward_vec, 0.5, 0.5, 1.0)
    save_json(tcp_order_path, tcp_order)

    # Diagnostics for quick validation
    top5 = list(zip(tcp_order[:5], [float(scores[ids.index(t)]) for t in tcp_order[:5]]))
    print(f"TCP order saved to {tcp_order_path}. Top-5: {top5}")

if __name__ == "__main__":
    main()
