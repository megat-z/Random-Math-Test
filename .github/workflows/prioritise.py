import os
import json
import numpy as np

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
    if not os.path.isfile(path):
        return np.zeros((len(ids), len(ids)), dtype=np.float32)
    m = load_json(path)
    arr = np.zeros((len(ids), len(ids)), dtype=np.float32)
    for i, id1 in enumerate(ids):
        for j, id2 in enumerate(ids):
            arr[i, j] = m.get(id1, {}).get(id2, 0.0)
    return arr

def get_latest_fault_matrix(dir_path, ids):
    files = sorted(
        [f for f in os.listdir(dir_path) if f.endswith(".json")],
        reverse=True
    )
    if not files:
        return np.zeros(len(ids), dtype=np.float32)
    latest_path = os.path.join(dir_path, files[0])
    try:
        mat = load_json(latest_path)
        return np.array([mat.get(id, 0.0) for id in ids], dtype=np.float32)
    except Exception:
        return np.zeros(len(ids), dtype=np.float32)

def prioritise_order(ids, input_mat, output_mat, reward_mat, alpha=0.5, beta=0.5, gamma=1.0):
    scores = alpha * np.sum(input_mat, axis=1) + beta * np.sum(output_mat, axis=1) + gamma * reward_mat
    order = [ids[i] for i in np.argsort(scores)[::-1]]
    return order

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
    reward_mat = get_latest_fault_matrix(fault_dir, ids)

    tcp_order = prioritise_order(ids, input_mat, output_mat, reward_mat)
    save_json(tcp_order_path, tcp_order)
    print(f"TCP order calculated and saved in {tcp_order_path}: {json.dumps(tcp_order)}")

if __name__ == "__main__":
    main()
