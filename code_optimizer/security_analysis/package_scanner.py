import re
from .vulnerability_db import UNSAFE_PACKAGES
from .cve_checker import check_package


def extract_packages_from_dockerfile(code):
   
    packages = []

    for line in code.splitlines():

        l = line.strip().lower()

        # apt
        apt_match = re.search(r"apt(-get)? install\s+(.+)", l)
        if apt_match:
            packages.extend(apt_match.group(2).split())

        # apk
        apk_match = re.search(r"apk add\s+(.+)", l)
        if apk_match:
            packages.extend(apk_match.group(1).split())

        # pip
        pip_match = re.search(r"pip install\s+(.+)", l)
        if pip_match:
            packages.extend(pip_match.group(1).split())

    return packages


def analyze_packages(packages):

    findings = []

    for pkg in packages:

        name = pkg.split("==")[0]

        # local check (local db -- see vulnerabilty_db)
        if name in UNSAFE_PACKAGES:
            findings.append(
                f"[OFFLINE] {name}: {UNSAFE_PACKAGES[name]}"
            )
        # online check - see cve_checkers
        online_vulns = check_package(name, ecosystem="PyPI")

        for vuln in online_vulns:
            if 'error' in vuln:
                findings.append(f"[ONLINE] Error checking {name}: {vuln['error']} ")
            else:
                findings.append(f"[ONLINE] {name} ({vuln['id']}):{vuln['summary']}")
            
    return findings

def scan_packages(code):
    if isinstance(code, list):
        code = "\n".join(code)
        
    metrics = {
        "root_user": 0,
        "exposed_ports": 0,
        "curl_pipe_shell": 0,
        "unsafe_packages": 0,
        "total_packages":0,
    }

    findings = []
    
    # docker patterns
    for line in code.splitlines():

        l = line.strip().lower()

        if l.startswith("user root"):
            metrics["root_user"] += 1

        if l.startswith("expose"):
            metrics["exposed_ports"] += 1

        if "curl" in l and "|" in l and "sh" in l:
            metrics["curl_pipe_shell"] += 1
    
    # package analysis
    packages = extract_packages_from_dockerfile(code)
    metrics["total_packages"] = len(packages)

    vuln_packages = analyze_packages(packages)

    metrics["unsafe_packages"] = len(vuln_packages)

    findings.extend(vuln_packages)
    return metrics, findings

def compare_packages(original_code, optimized_code):
    
    original_metrics, original_findings = scan_packages(original_code)
    optimized_metrics, optimized_findings = scan_packages(optimized_code)

    original_set = set(original_findings)
    optimized_set = set(optimized_findings)

    fixed_issues = sorted(original_set - optimized_set)
    new_issues = sorted(optimized_set - original_set)

    return {
        "fixed": fixed_issues,
        "new": new_issues, 
        "original": original_metrics,
        "optimized": optimized_metrics
    }