def analyze(code):
    """
    Static Dockerfile analysis from code string.
    """
    metrics = {
        "instructions": 0,
        "run_instructions": 0,
        "copy_instructions": 0
    }

    for raw_line in code.splitlines():
        line = raw_line.strip().upper()

        if not line or line.startswith("#"):
            continue

        metrics["instructions"] += 1

        if line.startswith("RUN"):
            metrics["run_instructions"] += 1

        if line.startswith(("COPY", "ADD")):
            metrics["copy_instructions"] += 1

    return metrics


def run(original_code, optimized_code):
    print("Static Dockerfile Analysis")

    orig = analyze(original_code)
    opt = analyze(optimized_code)

    print("\n Instruction Metrics (Original → Optimized):")
    for key in orig.keys():
        print(f"{key.replace('_',' ').title()}: {orig[key]} → {opt[key]}")

    print("\n Interpretation:")

    if opt["instructions"] < orig["instructions"]:
        print("- Fewer instructions reduce image layers and build I/O")

    if opt["run_instructions"] < orig["run_instructions"]:
        print("- Reduced RUN steps improve layer caching and energy efficiency")

    if opt["copy_instructions"] < orig["copy_instructions"]:
        print("- Fewer COPY/ADD steps reduce filesystem overhead")

    if opt == orig:
        print("- No structural changes detected")
