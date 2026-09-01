import yaml
from collections import Counter

from rich import containers


def analyze(doc):

    issues = []
    metrics = Counter()

    try:
        containers = doc["spec"]["template"]["spec"]["containers"]
    except Exception:
        return metrics, ["No containers found"]

    metrics["containers"] = len(containers)
    replicas = doc['spec'].get("replicas", 1)
    metrics["replicas"] = replicas

    if replicas < 2:
        issues.append("Low replica count reduces energy efficiency (poor scaling utilization)")

    for c in containers:
        if c.get('image', "").endswith(":latest"):
            issues.append('Use of :latest increases energy cost due to cache inefficiency')
        if 'resources' not in c:
            issues.append('Missing resource limits may lead to inefficient resource usage')
    return metrics, issues

def run(original_code, optimized_code):
    print("Static Energy Analysis (k8s)")

    try:
        orig_docs = list(yaml.safe_load_all(original_code))
        opt_docs = list(yaml.safe_load_all(optimized_code))
    except Exception:
        print("Invalid YAML")
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

    print('\n --- Original vs Optimized ---')
    keys = set(orig_m) | set(opt_m)
    for k in keys:
        print(f"{k}: {orig_m.get(k,0)} --> {opt_m.get(k,0)}")

    print('\n --- Improvements ---')
    if len(opt_i) < len(orig_i):
        print(f'Reduced issues {len(orig_i)} --> {len(opt_i)}')

    for i in set(opt_i):
        print(f'- {i}')