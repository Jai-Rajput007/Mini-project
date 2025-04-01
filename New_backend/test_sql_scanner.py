import asyncio
import json
import os
import sys
from app.services.enhanced_sql_scanner import EnhancedSQLScanner

async def test_scanner(url):
    """Test the SQL scanner and verify consolidation works."""
    print(f"Testing SQL scanner on {url}")
    print("=" * 80)
    
    # Create scanner and run scan
    scanner = EnhancedSQLScanner()
    vulnerabilities = await scanner.scan_url(url)
    
    # Display results
    print("\nScan Results:")
    print("-" * 80)
    print(f"Found {len(vulnerabilities)} unique SQL injection vulnerabilities:")
    
    # Group by location for better readability
    vulns_by_location = {}
    for vuln in vulnerabilities:
        location = vuln.get("location", "unknown")
        if location not in vulns_by_location:
            vulns_by_location[location] = []
        vulns_by_location[location].append(vuln)
    
    # Display grouped vulnerabilities
    for location, vulns in vulns_by_location.items():
        print(f"\nLocation: {location}")
        for i, vuln in enumerate(vulns, 1):
            print(f"  {i}. {vuln['name']} - {vuln['severity']}")
            print(f"     Description: {vuln['description']}")
            print(f"     Evidence: {vuln['evidence']}")
    
    # Save results to file
    output_file = "sql_scan_results.json"
    with open(output_file, "w") as f:
        json.dump(vulnerabilities, f, indent=2)
    
    print("\nResults saved to", output_file)
    print("=" * 80)
    return vulnerabilities

if __name__ == "__main__":
    # Get URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "http://testphp.vulnweb.com/"
    asyncio.run(test_scanner(url)) 