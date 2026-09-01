from collections import Counter
import re
import os

def run(original_code, optimized_code):
    """
    Static dependency analysis of Dockerfile.
    Checks for multiple RUN/COPY commands and suspicious patterns.
    """
    print(" Static Dependency Analysis ")

    code = original_code
    
    lines = [l.strip() for l in code.splitlines() if l.strip() and not l.strip().startswith('#')]
    if not lines:
        print("No code to analyse")
        return

    # docker-like instructions or generic commands
    instructions = []
    for l in lines:
        parts = l.split()
        if parts:
            instructions.append(parts[0].upper())

    counts = Counter(instructions)
    issues = []

    if counts["RUN"] > 1:
        issues.append("Multiple RUN instructions may increase dependency layers")
    if counts["COPY"] > 1:
        issues.append("Multiple COPY instructions may increase dependency layers")

    # apt-get detection
    for l in lines:
        if re.search(r"apt(-get)? install", l) and "rm -rf /var/lib/apt/lists" not in l:
            issues.append("apt-get install without cleanup increases dependencies")
    # pip detection
    for l in lines:
        if re.search(r"pip install", l) and "--no-cache-dir" not in l:
            issues.append("pip install without --no-cache-dir may bloat dependencies")

    print("\n Instruction count:")
    for k, v in counts.items():
        print(f"  {k}: {v}")

    print("\n Detected dependency issues:")
    if issues:
        for i in set(issues):
            print(f"- {i}")
    else:
        print("- No major dependency issues detected")