import os 
from .package_scanner import (scan_packages, compare_packages)

def run(original_code, optimized_code):

    print("=== Docker security comparison ===")
    original_metrics, original_findings = scan_packages(original_code)
    optimized_metrics, optimized_findings = scan_packages(optimized_code)

    report = compare_packages(original_code, optimized_code)

    print("\n--- Metrics (Original) ---")
    for k, v in original_metrics.items():
        print(f"- {k}: {v}")

    print("\n--- Metrix (Optimized) ---")
    for k, v in optimized_metrics.items():
        print(f"- {k}: {v}")

    print("\n Fixed Issues:")
    for f in report["fixed"]:
        print(f"- {f}")

    print("\n New Issues:")
    for n in report["new"]:
        print(f"- {n}")

    return {
        "original": original_metrics,
        "optimized": optimized_metrics,
        "diff": report
    }