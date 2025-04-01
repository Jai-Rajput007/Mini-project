import asyncio
import sys
import json
import os
from app.db.database import save_to_db, find_document
from app.services.report_service import ReportService

async def test_storage_functionality():
    """Test storage functionality with fallback JSON."""
    print("Testing storage functionality with fallback JSON...")
    
    # Force using fallback
    from app.db.database import _using_fallback
    globals()['_using_fallback'] = True
    
    # Initialize report service
    await ReportService.initialize()
    
    # Create a sample report
    test_data = {
        "scan_id": "test-scan-123",
        "url": "http://example.com",
        "timestamp": "2023-01-01T12:00:00",
        "scanners_used": ["sql_injection", "xss"],
        "status": "completed"
    }
    
    test_result = {
        "scan_id": "test-scan-123",
        "scan_duration": 10.5,
        "summary": {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 1,
            "info": 0
        },
        "findings": [
            {
                "id": "vuln-123",
                "name": "Test SQL Injection",
                "description": "This is a test vulnerability",
                "severity": "critical",
                "location": "http://example.com/test?id=1",
                "evidence": "Error message: SQL syntax error",
                "remediation": "Use parameterized queries"
            }
        ]
    }
    
    # Save test report
    print("\nSaving test report to fallback storage...")
    report_id = await ReportService.save_report(test_data, test_result)
    
    print(f"Report saved with ID: {report_id}")
    
    # Retrieve the report
    print("\nRetrieving report from fallback storage...")
    report = await ReportService.get_report(report_id)
    
    if report:
        print("Report retrieved successfully!")
        print(f"Report ID: {report.get('report_id')}")
        print(f"URL: {report.get('url')}")
        print(f"Vulnerability count: {report.get('vulnerabilities_count')}")
        
        # Export the report in different formats
        print("\nExporting report to different formats...")
        
        json_path = await ReportService.export_report(report_id, "json")
        if json_path:
            print(f"JSON export successful: {json_path}")
            
        txt_path = await ReportService.export_report(report_id, "txt")
        if txt_path:
            print(f"TXT export successful: {txt_path}")
            
        pdf_path = await ReportService.export_report(report_id, "pdf")
        if pdf_path:
            print(f"PDF export successful: {pdf_path}")
        else:
            print("PDF export failed - ReportLab might not be installed")
            
        # Check export files
        print("\nVerifying export files...")
        for path in [json_path, txt_path, pdf_path]:
            if path and os.path.exists(path):
                print(f"Export file exists: {path}")
                print(f"File size: {os.path.getsize(path)} bytes")
    else:
        print("Failed to retrieve report.")
        
    # Verify database fallback directory exists
    fallback_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db_fallback")
    if os.path.exists(fallback_dir):
        print(f"\nFallback directory exists: {fallback_dir}")
        collection_dirs = os.listdir(fallback_dir)
        print(f"Collections: {', '.join(collection_dirs)}")

if __name__ == "__main__":
    asyncio.run(test_storage_functionality()) 