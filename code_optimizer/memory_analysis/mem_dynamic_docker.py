import subprocess
import json
import tempfile
import os
import uuid


def build_and_measure(dockerfile_code, tag_prefix):
    """
    Builds a Docker image from Dockerfile code string
    and returns dynamic metrics.
    """
    temp_dir = tempfile.mkdtemp()
    dockerfile_path = os.path.join(temp_dir, "Dockerfile")

    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_code)

    image_tag = f"{tag_prefix}:{uuid.uuid4().hex[:8]}"

    subprocess.run(
        ["docker", "build", "-f", dockerfile_path, "-t", image_tag, temp_dir],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    result = subprocess.run(
        ["docker", "image", "inspect", image_tag],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)[0]

    metrics = {
        "image_size_mb": data["Size"] / (1024 * 1024),
        "layers": len(data["RootFS"]["Layers"])
    }

    return metrics


def run(original_code, optimized_code):
    print(" Dynamic Docker Analysis")

    orig = build_and_measure(original_code, "orig_img")
    opt = build_and_measure(optimized_code, "opt_img")

    print("\n Image Metrics (Original → Optimized):")
    print(f"Image size (MB): {orig['image_size_mb']:.2f} → {opt['image_size_mb']:.2f}")
    print(f"Layers: {orig['layers']} → {opt['layers']}")

    print("\n Interpretation:")

    if opt["image_size_mb"] < orig["image_size_mb"]:
        print("- Smaller image reduces storage, transfer energy and startup time")

    if opt["layers"] < orig["layers"]:
        print("- Fewer layers improve caching and reduce filesystem overhead")

    if opt == orig:
        print("- No significant dynamic differences detected")
