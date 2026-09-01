import re
from collections import Counter

def analyze(code):
    lines = [l.strip() for l in code.splitlines() if l.strip() and not l.strip().startswith("#")]
    instructions = [l.split()[0].upper() for l in lines]
    counts = Counter(instructions)

    issues = []

    if counts["RUN"] > 1:
        issues.append("Multiple RUN instructions increase layers and I/O")

    for l in lines:
        if re.search(r"FROM\s+\S+:latest", l):
            issues.append("Use of :latest tag reduces cache efficiency")
        if "apt-get install" in l and "rm -rf /var/lib/apt/lists" not in l:
            issues.append("apt-get without cleanup increases image size")

    return counts, issues


def run(original_code, optimized_code):
    print("Static Qualitative Energy Analysis (Dockerfile)")

    orig_counts, orig_issues = analyze(original_code)
    opt_counts, opt_issues = analyze(optimized_code)

    print("\n Instruction count (Original → Optimized):")
    keys = set(orig_counts) | set(opt_counts)
    for k in sorted(keys):
        print(f"  {k}: {orig_counts.get(k,0)} → {opt_counts.get(k,0)}")

    print("\n⚠ Qualitative findings (Optimized Dockerfile):")
    if opt_issues:
        for i in set(opt_issues):
            print(f"- {i}")
    else:
        print("- No major qualitative issues detected")

    print("\n Interpretation:")
    print("- Fewer layers and smaller images reduce build-time I/O and energy usage")
