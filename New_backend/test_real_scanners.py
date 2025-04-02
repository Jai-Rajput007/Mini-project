import requests
import json
import time
import sys

def test_scanners(backend_url, target_url):
    """
    Test if the real scanners are working properly
    
    Args:
        backend_url: The URL of the backend API
        target_url: The URL to scan for vulnerabilities
    """
    print(f"Testing scanners at {backend_url}")
    print(f"Will scan {target_url} for vulnerabilities")
    print("=" * 80)
    
    # 1. Start a scan with all scanners
    print("\n[1] Starting a scan with all scanners")
    scan_url = f"{backend_url}/api/v1/scanner/start"
    scan_data = {
        "url": target_url,
        "scanners": ["basic", "xss", "sql_injection", "http_methods", "file_upload"],
        "scanner_group": "advanced"
    }
    
    try:
        response = requests.post(scan_url, json=scan_data)
        if response.status_code == 200:
            scan_result = response.json()
            scan_id = scan_result.get('scan_id')
            print(f"  ✓ Scan started successfully with ID: {scan_id}")
            
            # 2. Poll for status
            print("\n[2] Polling scan status")
            completed = False
            max_polls = 20  # More polls for a full test
            poll_count = 0
            
            while poll_count < max_polls and not completed:
                poll_count += 1
                time.sleep(3)  # Wait 3 seconds between polls
                
                status_url = f"{backend_url}/api/v1/scanner/{scan_id}"
                status_response = requests.get(status_url)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    progress = status_data.get('progress', 0)
                    scanners_used = status_data.get('scanners_used', [])
                    
                    print(f"  Poll {poll_count}: Status = {status}, Progress = {progress}%")
                    print(f"  Active scanners: {', '.join(scanners_used)}")
                    
                    if status == "completed" or status == "failed" or status == "partially_completed":
                        completed = True
                        
                        # 3. Get results
                        print("\n[3] Getting scan results")
                        result_url = f"{backend_url}/api/v1/scanner/{scan_id}/result"
                        result_response = requests.get(result_url)
                        
                        if result_response.status_code == 200:
                            result_data = result_response.json()
                            
                            # Show summary
                            summary = result_data.get('summary', {})
                            print(f"\nVulnerability Summary:")
                            print(f"  Critical: {summary.get('critical', 0)}")
                            print(f"  High: {summary.get('high', 0)}")
                            print(f"  Medium: {summary.get('medium', 0)}")
                            print(f"  Low: {summary.get('low', 0)}")
                            print(f"  Info: {summary.get('info', 0)}")
                            
                            # Show which scanners were actually used
                            actual_scanners = result_data.get('scanners_used', [])
                            print(f"\nScanners actually used: {', '.join(actual_scanners)}")
                            
                            # Show vulnerabilities found
                            findings = result_data.get('findings', [])
                            if findings:
                                print(f"\nFound {len(findings)} vulnerabilities:")
                                for i, vuln in enumerate(findings[:5], 1):  # Show first 5
                                    print(f"  {i}. {vuln.get('name')} ({vuln.get('severity')})")
                                    print(f"     Location: {vuln.get('location')}")
                                
                                if len(findings) > 5:
                                    print(f"  ... and {len(findings) - 5} more vulnerabilities")
                            else:
                                print("\nNo vulnerabilities found.")
                            
                            # Save results to file
                            with open("test_results.json", "w") as f:
                                json.dump(result_data, f, indent=2)
                            print(f"\nSaved complete results to test_results.json")
                            
                            return True
                        else:
                            print(f"  ✗ Failed to get results: {result_response.status_code}")
                else:
                    print(f"  ✗ Failed to get status: {status_response.status_code}")
            
            if not completed:
                print("  ✗ Scan did not complete within expected time")
        else:
            print(f"  ✗ Failed to start scan: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  ✗ Error during scan: {str(e)}")
    
    return False

if __name__ == "__main__":
    backend_url = "http://localhost:8000"
    target_url = "http://testphp.vulnweb.com/"
    
    # Use command line args if provided
    if len(sys.argv) > 1:
        backend_url = sys.argv[1]
    if len(sys.argv) > 2:
        target_url = sys.argv[2]
    
    success = test_scanners(backend_url, target_url)
    if success:
        print("\n✓ Scanner test completed successfully!")
    else:
        print("\n✗ Scanner test failed!") 