import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional, Union
import asyncio
from pathlib import Path
import aiofiles

# For PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("ReportLab not available. PDF export will be disabled.")

# Import database functions
from ..db.database import (
    connect_to_mongo, 
    save_to_db, 
    find_document, 
    find_documents, 
    update_in_db,
    get_document_by_id,
    delete_document
)

class ReportService:
    """Service for managing vulnerability scan reports."""
    
    _cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
    
    @classmethod
    async def initialize(cls):
        """Initialize the report service."""
        # Ensure cache directory exists
        if not os.path.exists(cls._cache_dir):
            os.makedirs(cls._cache_dir)
            
        # Connect to MongoDB
        await connect_to_mongo()
    
    @classmethod
    async def save_report(cls, scan_data: Dict[str, Any], result_data: Dict[str, Any]) -> str:
        """
        Save a report to the database.
        
        Args:
            scan_data: The scan metadata
            result_data: The scan results
            
        Returns:
            str: The report ID
        """
        # Create a combined report document
        report = {
            "report_id": str(uuid.uuid4()),
            "scan_id": scan_data.get("scan_id", ""),
            "url": scan_data.get("url", ""),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "scan_timestamp": scan_data.get("timestamp", ""),
            "scan_duration": result_data.get("scan_duration", 0),
            "scanners_used": scan_data.get("scanners_used", []),
            "vulnerabilities_count": sum(result_data.get("summary", {}).values()),
            "summary": result_data.get("summary", {}),
            "status": "completed",
            "findings": result_data.get("findings", [])
        }
        
        # Save to MongoDB
        try:
            report_id = await save_to_db("reports", report)
            if report_id:
                print(f"Report saved to database with ID: {report_id}")
                report["_id"] = report_id
                return report_id
            else:
                # Fallback to local file if database save fails
                cls._save_report_to_file(report)
                return report["report_id"]
        except Exception as e:
            print(f"Error saving report to database: {e}")
            # Fallback to local file
            cls._save_report_to_file(report)
            return report["report_id"]
    
    @classmethod
    def _save_report_to_file(cls, report: Dict[str, Any]):
        """
        Save a report to a local file as fallback.
        
        Args:
            report: The report data
        """
        report_id = report.get("report_id", str(uuid.uuid4()))
        file_path = os.path.join(cls._cache_dir, f"{report_id}.json")
        
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"Report saved to file: {file_path}")
    
    @classmethod
    async def get_report(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a report from the database.
        
        Args:
            report_id: The ID of the report
            
        Returns:
            Optional[Dict[str, Any]]: The report if found, None otherwise
        """
        # Try to get from database
        try:
            # First try by report_id field
            report = await find_document("reports", {"report_id": report_id})
            if report:
                return report
                
            # Then try by _id field (MongoDB ObjectId)
            report = await get_document_by_id("reports", report_id)
            if report:
                return report
        except Exception as e:
            print(f"Error getting report from database: {e}")
        
        # Fallback to local file
        file_path = os.path.join(cls._cache_dir, f"{report_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        
        return None
    
    @classmethod
    async def get_reports(cls, limit: int = 10, skip: int = 0) -> Dict[str, Any]:
        """
        Get reports from the database.
        
        Args:
            limit: Maximum number of reports to return
            skip: Number of reports to skip
            
        Returns:
            Dict[str, Any]: Dictionary with reports and total count
        """
        try:
            # Get from database
            reports = await find_documents(
                "reports", 
                {}, 
                limit=limit, 
                skip=skip, 
                sort_field="timestamp", 
                sort_order=-1
            )
            
            # Get total count
            total = len(await find_documents("reports", {}))
            
            return {
                "reports": reports,
                "total": total
            }
        except Exception as e:
            print(f"Error getting reports from database: {e}")
            
            # Fallback to local files
            reports_files = os.listdir(cls._cache_dir)
            reports = []
            
            for file_name in reports_files[skip:skip+limit]:
                if file_name.endswith(".json"):
                    file_path = os.path.join(cls._cache_dir, file_name)
                    with open(file_path, "r") as f:
                        reports.append(json.load(f))
            
            return {
                "reports": reports,
                "total": len(reports_files)
            }
    
    @classmethod
    async def delete_report(cls, report_id: str) -> bool:
        """
        Delete a report from the database.
        
        Args:
            report_id: The ID of the report
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try to delete from database
            deleted = await delete_document("reports", {"report_id": report_id})
            
            if deleted:
                # Also delete local file if it exists
                file_path = os.path.join(cls._cache_dir, f"{report_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
                
            # Try as MongoDB ObjectId
            try:
                deleted = await delete_document("reports", {"_id": report_id})
                if deleted:
                    file_path = os.path.join(cls._cache_dir, f"{report_id}.json")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return True
            except:
                pass
                
            return False
        except Exception as e:
            print(f"Error deleting report from database: {e}")
            
            # Fallback to local file
            try:
                file_path = os.path.join(cls._cache_dir, f"{report_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            except:
                pass
                
            return False
    
    @classmethod
    async def export_report(cls, report_id: str, format_type: str = "json") -> Optional[str]:
        """
        Export a report to a specific format (JSON, PDF, TXT).
        
        Args:
            report_id: The ID of the report
            format_type: The format to export to (json, pdf, txt)
            
        Returns:
            Optional[str]: The path to the exported file if successful, None otherwise
        """
        # Get the report
        report = await cls.get_report(report_id)
        if not report:
            print(f"Report with ID {report_id} not found")
            return None
        
        # Create export directory if it doesn't exist
        export_dir = os.path.join(cls._cache_dir, "exports")
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # Create timestamp string for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export based on format
        if format_type.lower() == "json":
            return cls._export_to_json(report, export_dir, timestamp)
        elif format_type.lower() == "pdf":
            return cls._export_to_pdf(report, export_dir, timestamp)
        elif format_type.lower() == "txt":
            return cls._export_to_txt(report, export_dir, timestamp)
        else:
            print(f"Unsupported export format: {format_type}")
            return None
    
    @classmethod
    def _export_to_json(cls, report: Dict[str, Any], export_dir: str, timestamp: str) -> str:
        """Export report to JSON format."""
        report_id = report.get("report_id", "report")
        file_path = os.path.join(export_dir, f"{report_id}_{timestamp}.json")
        
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Report exported to JSON: {file_path}")
        return file_path
    
    @classmethod
    def _export_to_txt(cls, report: Dict[str, Any], export_dir: str, timestamp: str) -> str:
        """Export report to plain text format."""
        report_id = report.get("report_id", "report")
        file_path = os.path.join(export_dir, f"{report_id}_{timestamp}.txt")
        
        with open(file_path, "w") as f:
            # Write header
            f.write("="*80 + "\n")
            f.write(f"VULNERABILITY SCAN REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Write scan details
            f.write(f"Report ID: {report.get('report_id', 'N/A')}\n")
            f.write(f"Scan ID: {report.get('scan_id', 'N/A')}\n")
            f.write(f"URL: {report.get('url', 'N/A')}\n")
            f.write(f"Timestamp: {report.get('timestamp', 'N/A')}\n")
            f.write(f"Scan Duration: {report.get('scan_duration', 0):.2f} seconds\n")
            f.write(f"Scanners Used: {', '.join(report.get('scanners_used', []))}\n\n")
            
            # Write summary
            f.write("-"*80 + "\n")
            f.write("SUMMARY\n")
            f.write("-"*80 + "\n")
            
            summary = report.get("summary", {})
            if summary:
                for severity, count in summary.items():
                    f.write(f"{severity.capitalize()}: {count}\n")
                
                f.write(f"Total: {report.get('vulnerabilities_count', 0)}\n\n")
            
            # Write findings
            f.write("-"*80 + "\n")
            f.write("FINDINGS\n")
            f.write("-"*80 + "\n\n")
            
            for i, finding in enumerate(report.get("findings", []), 1):
                f.write(f"Finding #{i}: {finding.get('name', 'N/A')}\n")
                f.write(f"Severity: {finding.get('severity', 'N/A')}\n")
                f.write(f"Location: {finding.get('location', 'N/A')}\n")
                f.write(f"Description: {finding.get('description', 'N/A')}\n")
                f.write(f"Evidence: {finding.get('evidence', 'N/A')}\n")
                f.write(f"Remediation: {finding.get('remediation', 'N/A')}\n\n")
                f.write("-"*40 + "\n\n")
        
        print(f"Report exported to TXT: {file_path}")
        return file_path
    
    @classmethod
    def _export_to_pdf(cls, report: Dict[str, Any], export_dir: str, timestamp: str) -> Optional[str]:
        """Export report to PDF format."""
        if not PDF_AVAILABLE:
            print("ReportLab not available. Cannot export to PDF.")
            return None
            
        report_id = report.get("report_id", "report")
        file_path = os.path.join(export_dir, f"{report_id}_{timestamp}.pdf")
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=20
            )
            story.append(Paragraph("Vulnerability Scan Report", title_style))
            story.append(Spacer(1, 20))
            
            # Add scan details
            heading_style = ParagraphStyle(
                'Heading1',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12
            )
            story.append(Paragraph("Scan Details", heading_style))
            
            # Create a table for scan details
            data = [
                ["Report ID:", report.get("report_id", "N/A")],
                ["Scan ID:", report.get("scan_id", "N/A")],
                ["URL:", report.get("url", "N/A")],
                ["Timestamp:", report.get("timestamp", "N/A")],
                ["Scan Duration:", f"{report.get('scan_duration', 0):.2f} seconds"],
                ["Scanners Used:", ", ".join(report.get("scanners_used", []))]
            ]
            
            table = Table(data, colWidths=[120, 350])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Add summary
            story.append(Paragraph("Summary", heading_style))
            
            summary = report.get("summary", {})
            if summary:
                data = [["Severity", "Count"]]
                
                # Sort by severity level (critical, high, medium, low, info)
                severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
                sorted_summary = sorted(summary.items(), key=lambda x: severity_order.get(x[0], 5))
                
                for severity, count in sorted_summary:
                    data.append([severity.capitalize(), count])
                
                data.append(["Total", report.get("vulnerabilities_count", 0)])
                
                table = Table(data, colWidths=[120, 120])
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
                
                story.append(table)
            
            story.append(Spacer(1, 20))
            
            # Add findings
            story.append(Paragraph("Findings", heading_style))
            
            findings = report.get("findings", [])
            if findings:
                # Sort findings by severity
                severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
                findings_sorted = sorted(
                    findings, 
                    key=lambda x: severity_map.get(x.get("severity", "").lower(), -1),
                    reverse=True
                )
                
                for i, finding in enumerate(findings_sorted, 1):
                    # Add finding header
                    finding_name = finding.get("name", "N/A")
                    finding_severity = finding.get("severity", "N/A").upper()
                    
                    # Create different background colors based on severity
                    severity_color = colors.red
                    if finding_severity.lower() == "medium":
                        severity_color = colors.orange
                    elif finding_severity.lower() == "low":
                        severity_color = colors.yellow
                    elif finding_severity.lower() == "info":
                        severity_color = colors.blue
                    
                    # Add finding number and name
                    finding_title = f"Finding #{i}: {finding_name}"
                    finding_title_style = ParagraphStyle(
                        'FindingTitle',
                        parent=styles['Heading2'],
                        fontSize=14,
                        spaceAfter=6
                    )
                    story.append(Paragraph(finding_title, finding_title_style))
                    
                    # Create a table for finding details
                    data = [
                        ["Severity:", finding_severity],
                        ["Location:", finding.get("location", "N/A")],
                        ["Description:", finding.get("description", "N/A")],
                        ["Evidence:", finding.get("evidence", "N/A")],
                        ["Remediation:", finding.get("remediation", "N/A")]
                    ]
                    
                    table = Table(data, colWidths=[120, 350])
                    table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('BACKGROUND', (0, 0), (0, 0), severity_color),
                        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                    ]))
                    
                    story.append(table)
                    story.append(Spacer(1, 10))
            
            # Build PDF
            doc.build(story)
            print(f"Report exported to PDF: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"Error creating PDF report: {e}")
            return None
    
    @classmethod
    async def generate_report(cls, scan_id: str) -> Optional[str]:
        """
        Generate a report for a scan.
        
        Args:
            scan_id: The ID of the scan
            
        Returns:
            Optional[str]: The ID of the generated report if successful, None otherwise
        """
        # Get scan data directly from database to avoid circular imports
        scan_data = await find_document("scans", {"scan_id": scan_id})
        if not scan_data:
            print(f"Scan with ID {scan_id} not found")
            return None
            
        # Get scan result directly from database
        result_data = await find_document("scan_results", {"scan_id": scan_id})
        if not result_data:
            print(f"Result for scan with ID {scan_id} not found")
            return None
            
        # Create report
        report_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        # Basic report structure
        report = {
            "report_id": report_id,
            "scan_id": scan_id,
            "timestamp": timestamp,
            "title": f"Security Scan Report for {scan_data.get('url', 'Unknown URL')}",
            "summary": result_data.get("summary", {}),
            "findings": result_data.get("findings", []),
            "recommendations": []
        }
        
        # Add recommendations based on findings
        for finding in report["findings"]:
            if "remediation" in finding:
                report["recommendations"].append({
                    "title": f"Fix {finding.get('name', 'vulnerability')}",
                    "description": finding.get("remediation", ""),
                    "severity": finding.get("severity", "info")
                })
        
        # Save report to database
        try:
            await save_to_db("reports", report)
        except Exception as e:
            print(f"Error saving report to database: {e}")
            cls._save_report_to_file(report)
        
        return report_id 