import requests


OSV_URL = "https://api.osv.dev/v1/query"

def check_package(package_name, ecosystem="PyPI"):
    payload = {
        "package": {
            "name": package_name,
            "ecosystem": ecosystem
        }
    }

    try:
        res = requests.post(OSV_URL, json=payload, timeout=10)
        data = res.json()

        vulns = data.get("vulns", [])
        if not vulns:
            return []

        results = []
        for v in vulns:
            results.append({
                "id": v.get("id"),
                "summary": v.get("summary", "No description")
            })

        return results

    except Exception as e:
        return [{"error": str(e)}]