import asyncio
import os
import time
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from ..models.scan import ScanRequest, ScanResponse, ScanResult, ScanStatus, ScannerType, ScannerGroup, SCANNER_GROUPS
from ..db.database import save_to_db, update_in_db, find_document, find_documents, connect_to_mongo, get_db, delete_document
from .enhanced_sql_scanner import EnhancedSQLScanner
from .enhanced_http_scanner import EnhancedHTTPScanner
from .enhanced_file_upload_scanner import EnhancedFileUploadScanner
from .basic_scanner import BasicScanner
from .enhanced_xss_scanner import EnhancedXSSScanner
from .report_service import ReportService

class ScannerService:
    """
    Service for managing and running vulnerability scans.
    """
    
    # Dictionary to store active scan data
    _active_scans: Dict[str, Dict[str, Any]] = {}
    
    # Cache directory for scans if not using MongoDB
    _cache_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
    
    @classmethod
    async def initialize(cls):
        """Initialize the scanner service."""
        # Initialize storage
        cls._init_storage()
        
        # Connect to MongoDB
        await connect_to_mongo()
        
        # Initialize report service
        await ReportService.initialize()
    
    @classmethod
    async def start_scan(cls, scan_request: ScanRequest) -> ScanResponse:
        """
        Start a new scan.
        
        Args:
            scan_request: The scan request
            
        Returns:
            ScanResponse: The scan response
        """
        # Create a unique ID for this scan
        scan_id = str(uuid.uuid4())
        
        # Create scan record
        scan_record = {
            "scan_id": scan_id,
            "url": str(scan_request.url),
            "status": "queued",
            "timestamp": datetime.utcnow().isoformat(),
            "scanners_used": [scanner.value for scanner in scan_request.scanners] if scan_request.scanners else [],
            "progress": 0,
            "message": "Scan queued",
            "completed_scanners": 0,
            "total_scanners": len(scan_request.scanners) if scan_request.scanners else 0
        }
        
        # Save to database
        try:
            await save_to_db("scans", scan_record)
        except Exception as e:
            print(f"Error saving scan to database: {e}")
            cls._save_scan_to_file(scan_record)
        
        # Add to active scans
        cls._active_scans[scan_id] = scan_record
        
        # Start scan in background
        asyncio.create_task(cls._run_scan(
            scan_id, 
            str(scan_request.url), 
            [scanner.value for scanner in scan_request.scanners] if scan_request.scanners else [],
            scan_request.scan_params.dict() if scan_request.scan_params else None
        ))
        
        # Return response with scan ID
        return ScanResponse(
            scan_id=scan_id,
            url=str(scan_request.url),
            status=ScanStatus.QUEUED,
            timestamp=datetime.fromisoformat(scan_record["timestamp"]) if isinstance(scan_record["timestamp"], str) else scan_record["timestamp"],
            scanners_used=scan_record["scanners_used"],
            progress=0,
            message="Scan queued"
        )
    
    @classmethod
    async def _run_scan(cls, scan_id: str, url: str, scanners: List[str], scan_params: Dict[str, Any] = None) -> None:
        """
        Run a scan with the specified scanners. This is run as a background task.
        
        Args:
            scan_id: The ID of the scan
            url: The URL to scan
            scanners: List of scanners to use
            scan_params: Additional parameters for the scan
        """
        print(f"Running scan {scan_id} for URL: {url} with scanners: {scanners}")
        start_time = time.time()
        
        try:
            # Set a timeout for the entire scan process (5 minutes)
            async with asyncio.timeout(300):  # 5 minutes timeout
                # Update scan status to running
                await cls._update_scan_status(scan_id, ScanStatus.RUNNING, "Initializing scanners")
                
                # Initialize results
                results = []
                completed_scanners = 0
                total_scanners = len(scanners)
                scan_params = scan_params or {}
                
                # Track which scanners have been completed
                completed_scanner_types = set()
                
                # Update progress
                await cls._update_scan_progress(scan_id, 10)  # 10% - started
                
                # Run each scanner with individual timeouts
                for scanner_type in scanners:
                    scanner_start_time = time.time()
                    try:
                        # Set a timeout for each individual scanner (2 minutes)
                        async with asyncio.timeout(120):  # 2 minutes timeout per scanner
                            await cls._update_scan_message(scan_id, f"Running {scanner_type} scanner")
                            
                            # Get scanner vulnerabilities
                            scanner_result = []
                            
                            if scanner_type == ScannerType.BASIC:
                                from ..services.basic_scanner import BasicScanner
                                basic_scanner = BasicScanner()
                                scanner_result = await basic_scanner.scan_url(url)
                            
                            elif scanner_type == ScannerType.XSS:
                                from ..services.enhanced_xss_scanner import EnhancedXSSScanner
                                xss_scanner = EnhancedXSSScanner()
                                scanner_result = await xss_scanner.scan_url(url)
                            
                            elif scanner_type == ScannerType.SQL_INJECTION:
                                from ..services.enhanced_sql_scanner import EnhancedSQLScanner
                                sql_scanner = EnhancedSQLScanner()
                                scanner_result = await sql_scanner.scan_url(url)
                            
                            elif scanner_type == ScannerType.HTTP_METHODS:
                                from ..services.enhanced_http_scanner import EnhancedHTTPScanner
                                http_scanner = EnhancedHTTPScanner()
                                scanner_result = await http_scanner.scan_url(url)
                            
                            elif scanner_type == ScannerType.FILE_UPLOAD:
                                from ..services.enhanced_file_upload_scanner import EnhancedFileUploadScanner
                                file_upload_scanner = EnhancedFileUploadScanner()
                                scanner_result = await file_upload_scanner.scan_url(url)
                            
                            # Add results if any were found
                            if scanner_result and isinstance(scanner_result, list):
                                results.extend(scanner_result)
                            
                            # Mark scanner as completed
                            completed_scanners += 1
                            completed_scanner_types.add(scanner_type)
                            
                            # Calculate scanner duration
                            scanner_duration = time.time() - scanner_start_time
                            print(f"Scanner {scanner_type} completed in {scanner_duration:.2f} seconds")
                    
                    except asyncio.TimeoutError:
                        print(f"Scanner {scanner_type} timed out after 120 seconds")
                        # Still mark as completed but with timeout
                        completed_scanners += 1
                        # Add a timeout vulnerability
                        results.append({
                            "id": str(uuid.uuid4()),
                            "name": f"{scanner_type} Scanner Timeout",
                            "description": f"The {scanner_type} scanner timed out after 120 seconds",
                            "severity": "info",
                            "location": url,
                            "evidence": "Scanner timeout",
                            "remediation": "Try scanning with fewer scanners or contact support"
                        })
                    
                    except Exception as e:
                        print(f"Error in scanner {scanner_type}: {str(e)}")
                        completed_scanners += 1
                        # Add an error vulnerability
                        results.append({
                            "id": str(uuid.uuid4()),
                            "name": f"{scanner_type} Scanner Error",
                            "description": f"The {scanner_type} scanner encountered an error: {str(e)}",
                            "severity": "info",
                            "location": url,
                            "evidence": str(e),
                            "remediation": "Check logs for more details or contact support"
                        })
                    
                    # Update progress after each scanner (from 10% to 90% based on completion)
                    progress = 10 + int(80 * (completed_scanners / total_scanners))
                    await cls._update_scan_progress(scan_id, progress)
                
                # Calculate scan duration
                scan_duration = round(time.time() - start_time, 2)
                
                # Create the result even if no vulnerabilities were found
                scan_result = ScanResult(
                    scan_id=scan_id,
                    url=url,
                    timestamp=datetime.utcnow(),
                    scan_duration=scan_duration,
                    scanners_used=[s for s in scanners if s in completed_scanner_types],
                    findings=results
                )
                
                # Calculate summary
                summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
                for finding in results:
                    severity = finding.get("severity", "info").lower()
                    if severity in summary:
                        summary[severity] += 1
                
                # Add summary to result
                scan_result.summary = summary
                
                # Serialize the result
                result_data = json.loads(scan_result.model_dump_json())
                
                # Save to database or file
                try:
                    result_id = await save_to_db("scan_results", result_data)
                    if result_id:
                        await cls._update_scan_result(scan_id, result_id)
                    else:
                        cls._save_result_to_file(result_data)
                except Exception as e:
                    print(f"Error saving scan result: {str(e)}")
                    cls._save_result_to_file(result_data)
                
                # Generate report
                try:
                    report_id = await ReportService.generate_report(scan_id)
                    if report_id:
                        await cls._update_scan_report(scan_id, report_id)
                except Exception as e:
                    print(f"Error generating report: {str(e)}")
                
                # Update scan status to completed
                await cls._update_scan_status(scan_id, ScanStatus.COMPLETED, "Scan completed successfully")
                await cls._update_scan_progress(scan_id, 100)  # 100% - completed
        
        except asyncio.TimeoutError:
            # Overall scan timeout
            print(f"Scan {scan_id} timed out after 5 minutes")
            await cls._update_scan_status(scan_id, ScanStatus.FAILED, "Scan timed out after 5 minutes")
            
        except Exception as e:
            # Update scan status to failed
            print(f"Error during scan: {str(e)}")
            await cls._update_scan_status(scan_id, ScanStatus.FAILED, f"Scan failed: {str(e)}")
        
        finally:
            # Remove from active scans
            if scan_id in cls._active_scans:
                del cls._active_scans[scan_id]
    
    @classmethod
    def _init_storage(cls):
        """Initialize storage for scan data"""
        if not os.path.exists(cls._cache_dir):
            os.makedirs(cls._cache_dir)
            
        scans_dir = os.path.join(cls._cache_dir, "scans")
        if not os.path.exists(scans_dir):
            os.makedirs(scans_dir)
            
        results_dir = os.path.join(cls._cache_dir, "results")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
    
    @classmethod
    def _save_scan_to_file(cls, scan_record: Dict[str, Any]):
        """
        Save scan record to file.
        
        Args:
            scan_record: The scan record to save
        """
        scan_id = scan_record["scan_id"]
        file_path = os.path.join(cls._cache_dir, "scans", f"{scan_id}.json")
        
        with open(file_path, "w") as f:
            json.dump(scan_record, f, indent=2)
    
    @classmethod
    async def _update_scan_status(cls, scan_id: str, status: str, message: str = None):
        """
        Update the status of a scan.
        
        Args:
            scan_id: The ID of the scan
            status: The new status
            message: Optional message about the status
        """
        update_data = {"status": status}
        if message:
            update_data["message"] = message
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        success = await update_in_db("scans", {"scan_id": scan_id}, update_data)
        
        # Update in active scans cache
        if scan_id in cls._active_scans:
            cls._active_scans[scan_id]["status"] = status
            if message:
                cls._active_scans[scan_id]["message"] = message
        
        return success
    
    @classmethod
    def _save_result_to_file(cls, result_data: Dict[str, Any]):
        """
        Save scan result to file.
        
        Args:
            result_data: The result data to save
        """
        scan_id = result_data["scan_id"]
        file_path = os.path.join(cls._cache_dir, "results", f"{scan_id}.json")
        
        with open(file_path, "w") as f:
            json.dump(result_data, f, indent=2)
    
    @classmethod
    async def get_scan(cls, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get scan record.
        
        Args:
            scan_id: The ID of the scan
            
        Returns:
            Optional[Dict[str, Any]]: The scan record if found, None otherwise
        """
        # Try to get from active scans first
        if scan_id in cls._active_scans:
            return cls._active_scans[scan_id]
        
        # Try to get from database
        try:
            scan = await find_document("scans", {"scan_id": scan_id})
            if scan:
                return scan
        except Exception as e:
            print(f"Error getting scan from database: {e}")
        
        # Fallback to local storage
        file_path = os.path.join(cls._cache_dir, "scans", f"{scan_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        
        return None
    
    @classmethod
    async def get_result(cls, result_id: str) -> Optional[Dict[str, Any]]:
        """
        Get scan result.
        
        Args:
            result_id: The ID of the result
            
        Returns:
            Optional[Dict[str, Any]]: The scan result if found, None otherwise
        """
        # Try to get from database
        try:
            result = await find_document("scan_results", {"scan_id": result_id})
            if result:
                return result
        except Exception as e:
            print(f"Error getting result from database: {e}")
        
        # Fallback to local storage
        file_path = os.path.join(cls._cache_dir, "results", f"{result_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        
        return None
    
    @classmethod
    async def get_scans(cls, limit: int = 10, skip: int = 0) -> Dict[str, Any]:
        """
        Get all scans.
        
        Args:
            limit: Maximum number of scans to return
            skip: Number of scans to skip
            
        Returns:
            Dict[str, Any]: Dictionary with scans and total count
        """
        try:
            # Get from database
            scans = await find_documents("scans", {}, limit, skip)
            
            # Get total count
            total = len(await find_documents("scans", {}))
            
            return {
                "scans": scans,
                "total": total
            }
        except Exception as e:
            print(f"Error getting scans from database: {e}")
            
            # Fallback to local storage
            scans_dir = os.path.join(cls._cache_dir, "scans")
            if os.path.exists(scans_dir):
                scan_files = os.listdir(scans_dir)
                total = len(scan_files)
                
                scans = []
                for file_name in scan_files[skip:skip+limit]:
                    file_path = os.path.join(scans_dir, file_name)
                    with open(file_path, "r") as f:
                        scans.append(json.load(f))
                
                return {
                    "scans": scans,
                    "total": total
                }
            
            return {
                "scans": [],
                "total": 0
            }
    
    @staticmethod
    async def get_scan_status(scan_id: str) -> Optional[ScanResponse]:
        """
        Get the status of a scan.
        
        Args:
            scan_id: The ID of the scan
            
        Returns:
            Optional[ScanResponse]: The scan status if found, None otherwise
        """
        scan = await ScannerService.get_scan(scan_id)
        
        if not scan:
            return None
        
        response = ScanResponse(
            scan_id=scan["scan_id"],
            url=scan["url"],
            status=ScanStatus(scan["status"]),
            timestamp=datetime.fromisoformat(scan["timestamp"]),
            scanners_used=scan["scanners_used"],
            progress=scan.get("progress", 0),
            message=scan.get("message"),
            result_id=scan.get("result_id"),
            report_id=scan.get("report_id")
        )
        
        return response
    
    @staticmethod
    async def get_scan_result(scan_id: str) -> Optional[ScanResult]:
        """
        Get the result of a scan.
        
        Args:
            scan_id: The ID of the scan
            
        Returns:
            Optional[ScanResult]: The scan result if found, None otherwise
        """
        result_data = await ScannerService.get_result(scan_id)
        
        if not result_data:
            return None
        
        # Convert timestamp from string to datetime
        if isinstance(result_data.get("timestamp"), str):
            result_data["timestamp"] = datetime.fromisoformat(result_data["timestamp"])
        
        return ScanResult(**result_data)
    
    @staticmethod
    async def list_scans(limit: int = 10, skip: int = 0) -> List[ScanResponse]:
        """
        List all scans.
        
        Args:
            limit: Maximum number of scans to return
            skip: Number of scans to skip
            
        Returns:
            List[ScanResponse]: List of scan responses
        """
        result = await ScannerService.get_scans(limit, skip)
        scans = result["scans"]
        
        scan_responses = []
        for scan in scans:
            scan_responses.append(ScanResponse(
                scan_id=scan["scan_id"],
                url=scan["url"],
                status=ScanStatus(scan["status"]),
                timestamp=datetime.fromisoformat(scan["timestamp"]),
                scanners_used=scan["scanners_used"],
                progress=scan.get("progress", 0),
                message=scan.get("message"),
                result_id=scan.get("result_id"),
                report_id=scan.get("report_id")
            ))
        
        return scan_responses
    
    @classmethod
    async def _update_scan_message(cls, scan_id: str, message: str):
        """
        Update scan message.
        
        Args:
            scan_id: The ID of the scan
            message: The new message
        """
        if scan_id in cls._active_scans:
            current_status = cls._active_scans[scan_id]["status"]
            await cls._update_scan_status(scan_id, current_status, message=message)
            
            # Update progress based on scanner completion
            completed_scanners = cls._active_scans[scan_id].get("completed_scanners", 0)
            total_scanners = len(cls._active_scans[scan_id]["scanners_used"])
            progress = min(int((completed_scanners / total_scanners) * 100), 99) if total_scanners > 0 else 0
            await cls._update_scan_progress(scan_id, progress)
    
    @classmethod
    async def _update_scan_progress(cls, scan_id: str, progress: int):
        """
        Update scan progress.
        
        Args:
            scan_id: The ID of the scan
            progress: The new progress (0-100)
        """
        if scan_id in cls._active_scans:
            # Update in memory
            cls._active_scans[scan_id]["progress"] = progress
            
            # Update in database
            try:
                await update_in_db("scans", {"scan_id": scan_id}, {"progress": progress})
            except Exception as e:
                print(f"Error updating scan progress in database: {e}")
                # Fallback to local storage
                file_path = os.path.join(cls._cache_dir, "scans", f"{scan_id}.json")
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r") as f:
                            scan_record = json.load(f)
                        
                        scan_record["progress"] = progress
                        
                        with open(file_path, "w") as f:
                            json.dump(scan_record, f, indent=2)
                    except Exception as e2:
                        print(f"Error updating scan progress in file: {e2}")
    
    @classmethod
    async def _update_completed_scanners(cls, scan_id: str):
        """
        Increment the count of completed scanners.
        
        Args:
            scan_id: The ID of the scan
        """
        if scan_id in cls._active_scans:
            # Update in memory
            completed = cls._active_scans[scan_id].get("completed_scanners", 0) + 1
            cls._active_scans[scan_id]["completed_scanners"] = completed
            
            # Update in database
            try:
                await update_in_db("scans", {"scan_id": scan_id}, {"completed_scanners": completed})
            except Exception as e:
                print(f"Error updating completed scanners in database: {e}")
                # Fallback to local storage update is handled by _update_scan_progress
            
            # Update progress
            total_scanners = len(cls._active_scans[scan_id]["scanners_used"])
            progress = min(int((completed / total_scanners) * 100), 99) if total_scanners > 0 else 0
            await cls._update_scan_progress(scan_id, progress)
    
    @classmethod
    def _combine_results(cls, results: List[Dict[str, Any]]) -> ScanResult:
        """
        Combine results from multiple scanners.
        
        Args:
            results: List of vulnerabilities from all scanners
            
        Returns:
            ScanResult: Combined scan result
        """
        # Create a result with empty fields
        combined_result = ScanResult(
            scan_id="",
            url="",
            timestamp=datetime.utcnow(),
            scan_duration=0,
            scanners_used=[],
            vulnerabilities={},
            summary={
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            },
            findings=[]
        )
        
        # Add each vulnerability to the result
        for vuln in results:
            vuln_id = vuln.get("id", str(uuid.uuid4()))
            severity = vuln.get("severity", "info").lower()
            
            # Update vulnerability dictionary
            combined_result.vulnerabilities[vuln_id] = vuln
            
            # Update summary counts
            if severity in combined_result.summary:
                combined_result.summary[severity] += 1
            
            # Add to findings list
            combined_result.findings.append(vuln)
        
        return combined_result 
    
    @staticmethod
    async def export_report(report_id: str, format_type: str = "json") -> Optional[str]:
        """
        Export a report to the specified format.
        
        Args:
            report_id: The ID of the report
            format_type: The format to export to (pdf, json, txt)
            
        Returns:
            Optional[str]: The path to the exported file
        """
        return await ReportService.export_report(report_id, format_type)

    @staticmethod
    def _serialize_scan_data(scan_data):
        """
        Ensure all data is serializable by converting datetimes to ISO strings.
        
        Args:
            scan_data: The scan data dictionary
            
        Returns:
            dict: The serialized scan data
        """
        serialized = {}
        for key, value in scan_data.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = ScannerService._serialize_scan_data(value)
            elif isinstance(value, list):
                serialized[key] = [
                    ScannerService._serialize_scan_data(item) if isinstance(item, dict) else 
                    item.isoformat() if isinstance(item, datetime) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized 

    @classmethod
    async def _update_scan_result(cls, scan_id: str, result_id: str):
        """
        Update scan with result ID.
        
        Args:
            scan_id: The ID of the scan
            result_id: The ID of the result
        """
        if scan_id in cls._active_scans:
            # Update in memory
            cls._active_scans[scan_id]["result_id"] = result_id
            
            # Update in database
            try:
                await update_in_db("scans", {"scan_id": scan_id}, {"result_id": result_id})
            except Exception as e:
                print(f"Error updating scan result in database: {e}")
                # Fallback to local storage
                file_path = os.path.join(cls._cache_dir, "scans", f"{scan_id}.json")
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r") as f:
                            scan_record = json.load(f)
                        
                        scan_record["result_id"] = result_id
                        
                        with open(file_path, "w") as f:
                            json.dump(scan_record, f, indent=2)
                    except Exception as e2:
                        print(f"Error updating scan result in file: {e2}")
    
    @classmethod
    async def _update_scan_report(cls, scan_id: str, report_id: str):
        """
        Update scan with report ID.
        
        Args:
            scan_id: The ID of the scan
            report_id: The ID of the report
        """
        if scan_id in cls._active_scans:
            # Update in memory
            cls._active_scans[scan_id]["report_id"] = report_id
            
            # Update in database
            try:
                await update_in_db("scans", {"scan_id": scan_id}, {"report_id": report_id})
            except Exception as e:
                print(f"Error updating scan report in database: {e}")
                # Fallback to local storage
                file_path = os.path.join(cls._cache_dir, "scans", f"{scan_id}.json")
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r") as f:
                            scan_record = json.load(f)
                        
                        scan_record["report_id"] = report_id
                        
                        with open(file_path, "w") as f:
                            json.dump(scan_record, f, indent=2)
                    except Exception as e2:
                        print(f"Error updating scan report in file: {e2}")

    @classmethod
    async def get_scanner_info(cls) -> List[Dict[str, Any]]:
        """
        Get information about available scanners.
        
        Returns:
            List[Dict[str, Any]]: List of available scanners with details
        """
        scanners = [
            {
                "id": ScannerType.BASIC.value,
                "name": "Basic Scanner",
                "description": "Scans for basic security issues and information disclosure",
                "intensity": 1,
                "category": "essential"
            },
            {
                "id": ScannerType.XSS.value,
                "name": "XSS Scanner",
                "description": "Scans for Cross-Site Scripting vulnerabilities",
                "intensity": 2,
                "category": "essential"
            },
            {
                "id": ScannerType.SQL_INJECTION.value,
                "name": "SQL Injection Scanner",
                "description": "Scans for SQL Injection vulnerabilities",
                "intensity": 3,
                "category": "essential"
            },
            {
                "id": ScannerType.HTTP_METHODS.value,
                "name": "HTTP Methods Scanner",
                "description": "Checks for insecure HTTP methods",
                "intensity": 1,
                "category": "common"
            },
            {
                "id": ScannerType.FILE_UPLOAD.value,
                "name": "File Upload Scanner",
                "description": "Scans for file upload vulnerabilities",
                "intensity": 4,
                "category": "advanced"
            },
            {
                "id": ScannerType.ALL.value,
                "name": "Comprehensive Scan",
                "description": "Runs all available scanners",
                "intensity": 5,
                "category": "advanced"
            }
        ]
        return scanners