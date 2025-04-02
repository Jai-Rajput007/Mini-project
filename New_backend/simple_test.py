#!/usr/bin/env python
import requests
import json
import time
import sys

def test_basic_scan(api_url, test_url):
    """
    Test the basic scanner to verify the backend is working
    
    Args:
        api_url: Base URL of the API (e.g., http://localhost:8000)
        test_url: URL to scan for vulnerabilities
    """
    # Format URLs properly
    if not api_url.endswith('/'):
        api_url = api_url + '/'
    
    if not api_url.endswith('api/v1/'):
        api_url = api_url + 'api/v1/'
    
    print(f"Testing API at: {api_url}")
    print(f"Target URL to scan: {test_url}")
    print("-" * 80)
    
    # 1. Start a scan with only the basic scanner
    print("\n[1] Starting basic scan test")
    try:
        payload = {
            "url": test_url,
            "scanners": ["basic"],  # Only use basic scanner for quick test
            "scanner_group": "essential"
        }
        
        print(f"  Sending payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{api_url}scanner/start", json=payload)
        print(f"  Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Scan started with ID: {data.get('scan_id')}")
            scan_id = data.get('scan_id')
            
            # 2. Poll for scan status
            print("\n[2] Polling scan status")
            completed = False
            polls = 0
            max_polls = 30  # Wait longer for the scan to complete
            
            while not completed and polls < max_polls:
                polls += 1
                time.sleep(2)
                
                status_response = requests.get(f"{api_url}scanner/{scan_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    progress = status_data.get('progress', 0)
                    
                    print(f"  Poll {polls}: Status = {status}, Progress = {progress}%")
                    
                    if status in ["completed", "failed"]:
                        completed = True
                        
                        # 3. Check results
                        if status == "completed":
                            print("\n[3] Getting scan results")
                            results_response = requests.get(f"{api_url}scanner/{scan_id}/result")
                            
                            if results_response.status_code == 200:
                                results = results_response.json()
                                print(f"  Found {len(results.get('findings', []))} vulnerabilities")
                                
                                # Print the first 3 vulnerabilities
                                for i, vuln in enumerate(results.get('findings', [])[:3]):
                                    print(f"  - {vuln.get('name')} ({vuln.get('severity')})")
                                
                                print("  Test completed successfully!")
                            else:
                                print(f"  Failed to get results: {results_response.status_code}")
                                print(f"  Response: {results_response.text}")
                else:
                    print(f"  Error getting status: {status_response.text}")
            
            if not completed:
                print("  Scan did not complete within the polling period")
        else:
            print(f"  Failed to start scan: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  Error during test: {str(e)}")
    
    print("-" * 80)

if __name__ == "__main__":
    api_url = "http://localhost:8000"
    test_url = "http://testphp.vulnweb.com/"
    
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    if len(sys.argv) > 2:
        test_url = sys.argv[2]
    
    test_basic_scan(api_url, test_url) 