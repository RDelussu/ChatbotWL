import re
from collections import Counter

def analyze(code):
    lines = [l.strip() for l in code.splitlines() if l.strip() and not l.strip().startswith("#")]

    instructions = [l.split()[0].upper() for l in lines if l.split()]
    counts = Counter(instructions)

    issues = []

    if counts.get("RUN", 0) > 1:
        issues.append("Multiple RUN instructions increase layers and I/O")

    for l in lines:
        if re.search(r"FROM\s+\S+:latest", l):
            issues.append("Use of :latest tag reduces cache efficiency")
        if "apt-get install" in l and "rm -rf /var/lib/apt/lists" not in l:
            issues.append("apt-get without cleanup increases image size")

    return counts, list(set(issues))


def run(original_code, optimized_code):
    print(" Static Energy Analysis (Dockerfile)")

    counts_orig, issues_orig = analyze(original_code)
    counts_opt, issues_opt = analyze(optimized_code)

    print("\n Instruction Count (Original → Optimized):")
    all_keys = set(counts_orig) | set(counts_opt)
    for k in sorted(all_keys):
        print(f"{k}: {counts_orig.get(k,0)} → {counts_opt.get(k,0)}")

    print("\n Qualitative Issues Comparison:")

    removed = set(issues_orig) - set(issues_opt)
    added = set(issues_opt) - set(issues_orig)

    if removed:
        print("\n Issues resolved by optimization:")
        for i in removed:
            print(f"- {i}")

    if added:
        print("\n New issues introduced:")
        for i in added:
            print(f"- {i}")

    if not removed and not added:
        print("- No qualitative changes detected")

    print("\n Interpretation:")
    print("- Fewer RUN layers and smaller package footprints reduce build-time I/O and energy usage")
