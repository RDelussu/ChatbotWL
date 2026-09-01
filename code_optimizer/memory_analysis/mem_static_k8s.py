from importlib import resources

import yaml
from collections import Counter

from opentelemetry.proto.collector import metrics


def analyze(doc):

    issues = []
    metrics = Counter()

    try:
        containers =  doc["spec"]["template"]["spec"]["containers"]
    except Exception:
        return metrics, ["No containers found"]

    metrics["containers"] = len(containers)

    for c in containers:
        res = c.get('resources', {}).get('limits', {})

        if 'memory' not in res:
            issues.append('Missing memory limit')
        if 'ephemeral-storage' not in res:
            issues.append('Missing ephemeral storage limit')

    return metrics, issues


def run(original_code, optimized_code):
    print("Static Memory Analysis (k8s)")

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

    print('\n --- Memory metrics ---')
    for k in set(orig_m) | set(opt_m):
        print(f'{k}: {orig_m.get(k,0)} --> {opt_m.get(k,0)}')
    print('\n --- Issues ---')
    print(f'Issues reduced: {len(orig_i)} --> {len(opt_i)}')