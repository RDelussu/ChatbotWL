import subprocess
import json

def analyze_dynamic_docker_security(image_name):
    """
    Inspects security-relevant Docker image metadata.
    """
    result = subprocess.run(
        ["docker", "image", "inspect", image_name],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)[0]

    metrics = {
        "runs_as_root": int(data["Config"].get("User", "") in ("", "root")),
        "exposed_ports": len(data["Config"].get("ExposedPorts", {}) or {})
    }

    return metrics
