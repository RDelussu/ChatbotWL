import subprocess
import json
import os

def run(dockerfile_path, image_name="temp_dependency_image", context_path="."):
    """
    Dynamic dependency analysis of Dockerfile.
    Builds the image and reports size/layers as proxy for dependencies.
    """
    print(" Dynamic Dependency Analysis (Dockerfile) ")

    if not os.path.isfile(dockerfile_path):
        print("Dockerfile not found!")
        return

    print("\nBuilding image...")
    subprocess.run(
        ["docker", "build", "-f", dockerfile_path, "-t", image_name, context_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    print("Inspecting image layers...")
    result = subprocess.run(
        ["docker", "image", "inspect", image_name],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)[0]
    layers = data["RootFS"]["Layers"]
    size = data["Size"]

    print(f"\nImage size: {size / (1024*1024):.2f} MB")
    print(f"Number of layers: {len(layers)}")

    print("\nInterpretation:")
    print("- More layers or larger size may indicate heavy or redundant dependencies")
