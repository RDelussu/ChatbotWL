import yaml
from collections import Counter

from cryptography.hazmat.primitives.twofactor import totp


def analyzer(doc):

    issues = []
    metrics = Counter()

    if not isinstance(doc, dict):
        return metrics, ["Invalid YAML structure"]

    try:
        containers = doc["spec"]["template"]["spec"]["containers"]
    except Exception:
        return metrics, ["No containers found"]

    metrics['containers'] = len(containers)

    for c in containers:
        image = c.get("image", "")

        if ":latest" in image:
            issues.append("Using :latest tag may cause unstable dependencies")
        
        if "alpine" not in image and 'slim' not in image:
            issues.append('Heavy base image detected')

    return metrics, issues

def run(original_code, optimized_code):
    print("Static Dependency Analysis (k8s)")

    try:
        orig_docs = list(yaml.safe_load(original_code))
        opt_docs = list(yaml.safe_load(optimized_code))
    except Exception:
        print("Invalid YAML")
        return

    orig_m, orig_i = Counter(), []
    opt_m, opt_i = Counter(), []

    for d in orig_docs:
        m, i = analyzer(d)
        orig_m.update(m)
        orig_i.extend(i)

    for d in opt_docs:
        m, i = analyzer(d)
        opt_m.update(m)
        opt_i.extend(i)

    print("--- Dependencyy metrics ---")
    for k in set(orig_m) | set(opt_m):
        print(f'{k}: {orig_m.get(k,0)} --> {opt_m.get(k,0)}')

    print('\n--- Issues ---')
    print(f'{len(orig_i)} --> {len(opt_i)}')