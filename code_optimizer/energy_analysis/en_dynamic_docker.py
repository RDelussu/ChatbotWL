import subprocess
import json
import tempfile
import os
import uuid

def build_and_measure(dockerfile_content, tag):
    with tempfile.TemporaryDirectory() as tmpdir:
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")

        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        subprocess.run(
            ["docker", "build", "-f", dockerfile_path, "-t", tag, tmpdir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        result = subprocess.run(
            ["docker", "image", "inspect", tag],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)[0]
        layers = len(data["RootFS"]["Layers"])
        size_mb = data["Size"] / (1024 * 1024)

        return layers, size_mb


def run(original_code, optimized_code):
    print(" Dynamic Energy Analysis (Dockerfile)")

    tag_orig = f"analysis_orig_{uuid.uuid4().hex[:8]}"
    tag_opt  = f"analysis_opt_{uuid.uuid4().hex[:8]}"

    try:
        print("\n Building original image...")
        layers_orig, size_orig = build_and_measure(original_code, tag_orig)

        print("Building optimized image...")
        layers_opt, size_opt = build_and_measure(optimized_code, tag_opt)

        print("\n Results (Original → Optimized):")
        print(f"Image size: {size_orig:.2f} MB → {size_opt:.2f} MB")
        print(f"Layers: {layers_orig} → {layers_opt}")

        size_diff = size_orig - size_opt
        layer_diff = layers_orig - layers_opt

        print("\n Interpretation:")
        if size_diff > 0:
            print(f"- Image reduced by {size_diff:.2f} MB (less I/O, better energy efficiency)")
        elif size_diff < 0:
            print(f"- Image increased by {abs(size_diff):.2f} MB (potentially worse energy usage)")
        else:
            print("- Image size unchanged")

        if layer_diff > 0:
            print(f"- {layer_diff} fewer layers → better caching and lower storage overhead")
        elif layer_diff < 0:
            print(f"- {abs(layer_diff)} additional layers → potential inefficiency")
        else:
            print("- Number of layers unchanged")

    except Exception as e:
        print(f"Analysis failed: {e}")

    finally:
        # cleanup
        subprocess.run(["docker", "rmi", "-f", tag_orig], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "rmi", "-f", tag_opt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
