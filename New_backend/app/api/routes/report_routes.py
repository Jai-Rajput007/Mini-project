from fastapi import APIRouter, HTTPException, Query, Path, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Dict, Any, Optional
import os
import asyncio

from ...services.report_service import ReportService
from ...services.scanner_service import ScannerService

router = APIRouter()

@router.get("/{report_id}", response_model=Dict[str, Any])
async def get_report(report_id: str = Path(..., description="The ID of the report")):
    """
    Get a report by ID.
    
    Args:
        report_id: The ID of the report
        
    Returns:
        Dict[str, Any]: The report data
    """
    try:
        report = await ReportService.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting report: {str(e)}")

@router.get("/{report_id}/export/{format_type}")
async def export_report(
    background_tasks: BackgroundTasks,
    report_id: str = Path(..., description="The ID of the report"),
    format_type: str = Path(..., description="The format to export to (pdf, json, txt)")
):
    """
    Export a report to a specific format.
    
    Args:
        report_id: The ID of the report
        format_type: The format to export to (pdf, json, txt)
        
    Returns:
        FileResponse: The exported file
    """
    try:
        # Validate format type
        if format_type.lower() not in ["pdf", "json", "txt"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format_type}")
        
        # Check if report exists
        report = await ReportService.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found")
        
        # Export report (this can take time for large reports)
        file_path = await ReportService.export_report(report_id, format_type.lower())
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to export report")
        
        # Set up clean-up task for temporary file
        # This will delete the file after it has been sent to the client
        def remove_file(path: str):
            try:
                # Wait a bit to ensure the file has been sent
                asyncio.sleep(60)
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Error removing file {path}: {e}")
        
        background_tasks.add_task(remove_file, file_path)
        
        # Create a meaningful filename for the download
        filename = os.path.basename(file_path)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=get_media_type(format_type.lower())
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")

@router.get("/list")
async def list_reports(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of reports to return"),
    skip: int = Query(0, ge=0, description="Number of reports to skip")
):
    """
    List all reports.
    
    Args:
        limit: Maximum number of reports to return
        skip: Number of reports to skip
        
    Returns:
        Dict[str, Any]: Dictionary with reports and total count
    """
    try:
        result = await ReportService.get_reports(limit, skip)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")

@router.delete("/{report_id}")
async def delete_report(report_id: str = Path(..., description="The ID of the report")):
    """
    Delete a report.
    
    Args:
        report_id: The ID of the report
        
    Returns:
        Dict[str, Any]: Success message
    """
    try:
        success = await ReportService.delete_report(report_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found or could not be deleted")
        return {"message": f"Report {report_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting report: {str(e)}")

def get_media_type(format_type: str) -> str:
    """Get the media type for a file format."""
    if format_type == "pdf":
        return "application/pdf"
    elif format_type == "json":
        return "application/json"
    elif format_type == "txt":
        return "text/plain"
    else:
        return "application/octet-stream" 