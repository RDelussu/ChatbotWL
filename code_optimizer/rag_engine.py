import os
import re
import requests

class CodeRAGEngine:

    def __init__(self, db_path=None):
       ### per ora non serve 
       pass

    def extract_packages(self, code_query: str, language: str):
        """
        Parameters:
        - code_query: str
            source code
        - language: str
            programming language
        Returns:
        - detected: list of dicts
            list of vulnerable packages
        """
        detected = []

        if 'dockerfile' in language.lower():
            base_image = re.search(r'(?i)FROM\s+([\w\.\/:-]+)', code_query)
            if base_image:
                img_name = base_image.group(1)
                if ':' in img_name:
                    name, version = img_name.split (':', 1)
                    detected.append({'name':name, 'version': version})
        elif 'yaml' in language.lower() or 'kubernetes' in language.lower():
            images = re.findall(r'(?i)image:\s+([\w\.\/:-]+)', code_query)
            for img in images: # todo verificare di non sovraccaricare qui
                name, version = img.split(':', 1)
                detected.append({'name':name, 'version': version})
        else:
            print('Programming Language unknown')
        return detected


    def retrieve_context(self, code_query: str, language: str = 'dockerfile',  n_results: int = 10):
        """
        Parameters:
        - code_query: str
            source code 
        - language: str
            programming language
        - n_results: int
            number of retrieved results
        """
        packages = self.extract_packages(code_query, language)
        vulnerability_reports = []

        for pkg in packages:
            payload = {
                'version':pkg['version'],
                'package':{'name': pkg['name']}
            }

            try:
                response = requests.post("https://api.osv.dev/v1/query", json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'vulns' in data:
                        for vuln in data['vuln'][:n_results]:
                            cve_id = vuln.get('id', 'Unknown ID')
                            summary = vuln.get('summary', 'No summary available')
                            details = vuln.get('details', 'No details provided')

                            short_details = details[:200] + '...' if len(details) > 200 else details
                            vulnerability_reports.append(
                                f"[-] SECURITY ALERT: {cve_id}\n"
                                f"Component: {pkg['name']} (version {pkg['version']})\n"
                                f"Issue: {summary}\n"
                                f"Description: {short_details}"
                            )
            except Exception as e:
                continue
        if vulnerability_reports:
            return '\n\n---\n\n'.join(vulnerability_reports)

        return 'No known critical CVEs found in the online OSV Database for the detected components.'