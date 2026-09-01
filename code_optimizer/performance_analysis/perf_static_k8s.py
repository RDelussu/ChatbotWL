import yaml
from collections import Counter

def analyze(doc):
    issues = []
    metrics = Counter()

    try:
        spec = doc["spec"]["template"]["spec"]
        containers = spec["containers"]
    except Exception:
        return metrics, ["No containers found"]

    metrics["containers"] = len(containers)

    replicas = doc["spec"].get("replicas", 1)

    if replicas == 1:
        issues.append("Single replica may reduce performance scalability")

    for c in containers:
        if "livenessProbe" not in c:
            issues.append("Missing livenessProbe may reduce runtime reliability")
        if "readinessProbe" not in c:
            issues.append("Missing readinessProbe may impact load balancing performance")

    return metrics, issues

def run(original_code, optimized_code):
    print("Static Performance Analysis (k8s)")

    try:
        orig_docs = list(yaml.safe_load_all(original_code))
        opt_docs = list(yaml.safe_load_all(optimized_code))
    except Exception as e:
        print(f"Invalid YAML: {e}")
        return

    orig_m, orig_i = Counter(), []
    opt_m, opt_i = Counter(), []

    for d in orig_docs:
        m, i = analyze(d)
        orig_m.update(m)
        orig_i.extend(i)
    for d in opt_docs:
        m, i = analyze(d)
        opt_m.update(m)
        opt_i.extend(i)

    print("\n Performance metrics:")
    for k in set(orig_m) | set(opt_m):
        print(f"{k}: {orig_m.get(k, 0)} → {opt_m.get(k, 0)}")

    print("\n--- Improvements ---")
    print(f"Issues: {len(orig_i)} → {len(opt_i)}")