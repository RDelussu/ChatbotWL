

def extract_images_from_yaml(code):

    images = []

    for line in code.splitlines():

        line.strip()

        if "image:" in line:
            image = line.split("image:")[1].strip()

            images.append(image)

    return images

def analyze_images(images):

    findings = []

    for img in images:

        # latest tag risk
        if "latest" in img:
            findings.append(f"{img} uses 'latest' tag (unpredictable deployments)")
        
        # missing tag
        if ":" not in img:
            findings.append(f"{img} has no version tag (unsafe / non-reproducible)")

        # suspicious base images
        base = img.split(":")[0]

        risky_images = ["alpine", "ubuntu", "debian"]

        if base in risky_images and ":latest" in img:
            findings.append(f"{img} uses risky image with latest tag")

    return findings if findings else ["No image security issues detected"]

def scan_images(code):
    images = extract_images_from_yaml(code)
    return analyze_images(images)

def scan_k8s(code):
    findings = []

    # image scan
    findings.extend(scan_images(code))

    # other check YAML
    for line in code.splitlines():
        l = line.lower()

        if "privileged: true" in l:
            findings.append("privileged container detected")

        if "runasuser: 0" in l:
            findings.append("container running as root")

        if "hostnetwork: true" in l:
            findings.append("host network enabled")

    return findings

def compare_security(original_code, optimized_code):

    original = scan_k8s(original_code)
    optimized = scan_k8s(optimized_code)

    original_set = set(original)
    optimized_set = set(optimized)

    return {
        "fixed": sorted(original_set - optimized_set),
        "new_issues": sorted(optimized_set - original_set),
        "original": original,
        "optimized": optimized
    }