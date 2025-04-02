#!/usr/bin/env python
import requests
import json
import time
import sys

def test_api(api_url, test_url):
    """
    Test the scanning API functionality
    
    Args:
        api_url: Base URL of the API (e.g., http://localhost:8000/api/v1)
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
    
    # 1. Start a scan
    print("\n[1] Starting scan test")
    try:
        payload = {
            "url": test_url,
            "scanners": ["basic", "http_methods"],  # Start with minimal scanners for quicker test
            "scanner_group": "common"
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
            max_polls = 5
            
            while not completed and polls < max_polls:
                polls += 1
                time.sleep(2)
                
                status_response = requests.get(f"{api_url}scanner/{scan_id}")
                print(f"  Poll {polls}: Status {status_response.status_code}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    progress = status_data.get('progress', 0)
                    
                    print(f"  Status: {status}, Progress: {progress}%")
                    
                    if status in ["completed", "failed"]:
                        completed = True
                        
                        # 3. Check results
                        if status == "completed":
                            print("\n[3] Getting scan results")
                            results_response = requests.get(f"{api_url}scanner/{scan_id}/result")
                            
                            if results_response.status_code == 200:
                                results = results_response.json()
                                print(f"  Found {len(results.get('findings', []))} vulnerabilities")
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
    
    test_api(api_url, test_url) 