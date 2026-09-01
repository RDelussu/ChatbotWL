import yaml
from .images_scanner import compare_security


def run(original_code, optimized_code):

    print("Kubernetes Security - Analysis and Comparison")

    report = compare_security(original_code, optimized_code)

    print("\n Fixed Issues")
    for f in report["fixed"]:
        print(f"- {f}")

    print("\n New Issues")
    for n in report["new_issues"]:
        print(f"- {n}")

    print("\n Original Findings")
    for o in report["original"]:
        print(f"- {o}")

    print("\n Optimized Findings")
    for o in report["optimized"]:
        print(f"- {o}")