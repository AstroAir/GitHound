"""
Integration features API for GitHound.

Provides export capabilities, webhook management, batch operations,
and other integration features.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..schemas import OutputFormat
from ..utils.export import ExportManager
from .auth import require_admin, require_user
from .comprehensive_api import ApiResponse, get_request_id, validate_repo_path
from .rate_limiting import export_rate_limit_dependency, get_limiter
from .webhooks import (
    EventTypes,
    WebhookEndpoint,
    WebhookEvent,
    webhook_manager,
    trigger_repository_event
)

# Create router
router = APIRouter(prefix="/api/v3/integration", tags=["integration"])
limiter = get_limiter()

# Global state for operations
active_exports: Dict[str, Dict[str, Any]] = {}
batch_operations: Dict[str, Dict[str, Any]] = {}


# Export Models
class ExportRequest(BaseModel):
    """Request for data export."""
    export_type: str = Field(..., description="Type of data to export")
    format: OutputFormat = Field(OutputFormat.JSON, description="Export format")
    repo_path: Optional[str] = Field(None, description="Repository path")
    search_id: Optional[str] = Field(None, description="Search ID to export")
    include_metadata: bool = Field(True, description="Include metadata")
    filters: Optional[Dict[str, Any]] = Field(None, description="Export filters")
    filename: Optional[str] = Field(None, description="Custom filename")


class BatchOperationRequest(BaseModel):
    """Request for batch operations."""
    operation_type: str = Field(..., description="Type of batch operation")
    repositories: List[str] = Field(..., description="Repository paths")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    parallel: bool = Field(True, description="Execute operations in parallel")
    max_concurrent: int = Field(5, ge=1, le=20, description="Maximum concurrent operations")


class WebhookCreateRequest(BaseModel):
    """Request to create a webhook endpoint."""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret")
    active: bool = Field(True, description="Whether endpoint is active")


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook endpoint."""
    url: Optional[str] = Field(None, description="Webhook URL")
    events: Optional[List[str]] = Field(None, description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret")
    active: Optional[bool] = Field(None, description="Whether endpoint is active")


# Export Endpoints

@router.post("/export", response_model=ApiResponse)
@limiter.limit("5/minute")
async def create_export(
    request: Request,
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Create a data export operation.
    
    Supports exporting repository data, search results, analysis reports
    in various formats (JSON, YAML, CSV, XML).
    """
    try:
        # Generate export ID
        export_id = str(uuid.uuid4())
        
        # Validate repository if specified
        if export_request.repo_path:
            await validate_repo_path(export_request.repo_path)
        
        # Initialize export state
        export_state = {
            "id": export_id,
            "status": "queued",
            "progress": 0.0,
            "message": "Export queued",
            "user_id": current_user["user_id"],
            "started_at": datetime.now(),
            "request": export_request.dict(),
            "download_url": None
        }
        active_exports[export_id] = export_state
        
        # Start export in background
        background_tasks.add_task(
            perform_export_operation,
            export_id,
            export_request,
            current_user["user_id"]
        )
        
        return ApiResponse(
            success=True,
            message="Export operation started",
            data={
                "export_id": export_id,
                "status": "queued",
                "export_type": export_request.export_type,
                "format": export_request.format.value
            },
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create export: {str(e)}"
        )


@router.get("/export/{export_id}/status", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_export_status(
    request: Request,
    export_id: str,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Get the status of an export operation."""
    if export_id not in active_exports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    export_state = active_exports[export_id]
    
    # Check access
    if (export_state["user_id"] != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this export"
        )
    
    return ApiResponse(
        success=True,
        message="Export status retrieved",
        data={
            "export_id": export_id,
            "status": export_state["status"],
            "progress": export_state["progress"],
            "message": export_state["message"],
            "started_at": export_state["started_at"],
            "download_url": export_state.get("download_url"),
            "error": export_state.get("error")
        },
        request_id=request_id
    )


@router.get("/export/{export_id}/download")
@limiter.limit("10/minute")
async def download_export(
    request: Request,
    export_id: str,
    current_user: Dict[str, Any] = Depends(require_user)
) -> FileResponse:
    """Download the exported file."""
    if export_id not in active_exports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    export_state = active_exports[export_id]
    
    # Check access
    if (export_state["user_id"] != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this export"
        )
    
    if export_state["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Export not completed"
        )
    
    file_path = export_state.get("file_path")
    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    filename = export_state.get("filename", f"export_{export_id}")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


# Webhook Management Endpoints

@router.post("/webhooks", response_model=ApiResponse)
@limiter.limit("10/minute")
async def create_webhook(
    request: Request,
    webhook_request: WebhookCreateRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Create a new webhook endpoint."""
    try:
        # Generate webhook ID
        webhook_id = str(uuid.uuid4())
        
        # Create webhook endpoint
        endpoint = WebhookEndpoint(
            id=webhook_id,
            url=webhook_request.url,
            events=webhook_request.events,
            secret=webhook_request.secret,
            active=webhook_request.active
        )
        
        # Add to webhook manager
        webhook_manager.add_endpoint(endpoint)
        
        return ApiResponse(
            success=True,
            message="Webhook endpoint created successfully",
            data={
                "webhook_id": webhook_id,
                "url": webhook_request.url,
                "events": webhook_request.events,
                "active": webhook_request.active
            },
            request_id=request_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook: {str(e)}"
        )


@router.get("/webhooks", response_model=ApiResponse)
@limiter.limit("30/minute")
async def list_webhooks(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """List all webhook endpoints."""
    endpoints = webhook_manager.list_endpoints()
    
    webhook_data: list[Any] = []
    for endpoint in endpoints:
        stats = webhook_manager.get_endpoint_stats(endpoint.id)
        webhook_data.append({
            "id": endpoint.id,
            "url": endpoint.url,
            "events": endpoint.events,
            "active": endpoint.active,
            "created_at": endpoint.created_at,
            "last_delivery": endpoint.last_delivery,
            "failure_count": endpoint.failure_count,
            "stats": stats
        })
    
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(webhook_data)} webhook endpoints",
        data={"webhooks": webhook_data, "total_count": len(webhook_data)},
        request_id=request_id
    )


@router.put("/webhooks/{webhook_id}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def update_webhook(
    request: Request,
    webhook_id: str,
    webhook_update: WebhookUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Update a webhook endpoint."""
    endpoint = webhook_manager.get_endpoint(webhook_id)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    # Update endpoint
    updates: dict[str, Any] = {}
    if webhook_update.url is not None:
        updates["url"] = webhook_update.url
    if webhook_update.events is not None:
        updates["events"] = webhook_update.events
    if webhook_update.secret is not None:
        updates["secret"] = webhook_update.secret
    if webhook_update.active is not None:
        updates["active"] = webhook_update.active
    
    success = webhook_manager.update_endpoint(webhook_id, updates)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update webhook"
        )
    
    return ApiResponse(
        success=True,
        message="Webhook updated successfully",
        data={"webhook_id": webhook_id, "updates": updates},
        request_id=request_id
    )


@router.delete("/webhooks/{webhook_id}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def delete_webhook(
    request: Request,
    webhook_id: str,
    current_user: Dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Delete a webhook endpoint."""
    success = webhook_manager.remove_endpoint(webhook_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return ApiResponse(
        success=True,
        message="Webhook deleted successfully",
        data={"webhook_id": webhook_id},
        request_id=request_id
    )


# Batch Operations Endpoints

@router.post("/batch", response_model=ApiResponse)
@limiter.limit("3/minute")
async def create_batch_operation(
    request: Request,
    batch_request: BatchOperationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Create a batch operation across multiple repositories.

    Supports batch analysis, search, export, and other operations
    across multiple repositories simultaneously.
    """
    try:
        # Generate batch operation ID
        batch_id = str(uuid.uuid4())

        # Validate repositories
        for repo_path in batch_request.repositories:
            await validate_repo_path(repo_path)

        # Initialize batch operation state
        batch_state = {
            "id": batch_id,
            "status": "queued",
            "progress": 0.0,
            "message": "Batch operation queued",
            "user_id": current_user["user_id"],
            "started_at": datetime.now(),
            "operation_type": batch_request.operation_type,
            "repositories": batch_request.repositories,
            "parameters": batch_request.parameters,
            "results": {},
            "completed_count": 0,
            "failed_count": 0,
            "total_count": len(batch_request.repositories)
        }
        batch_operations[batch_id] = batch_state

        # Start batch operation in background
        background_tasks.add_task(
            perform_batch_operation,
            batch_id,
            batch_request,
            current_user["user_id"]
        )

        return ApiResponse(
            success=True,
            message="Batch operation started",
            data={
                "batch_id": batch_id,
                "status": "queued",
                "operation_type": batch_request.operation_type,
                "repository_count": len(batch_request.repositories),
                "parallel": batch_request.parallel
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch operation: {str(e)}"
        )


@router.get("/batch/{batch_id}/status", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_batch_status(
    request: Request,
    batch_id: str,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Get the status of a batch operation."""
    if batch_id not in batch_operations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch operation not found"
        )

    batch_state = batch_operations[batch_id]

    # Check access
    if (batch_state["user_id"] != current_user["user_id"] and
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this batch operation"
        )

    return ApiResponse(
        success=True,
        message="Batch operation status retrieved",
        data={
            "batch_id": batch_id,
            "status": batch_state["status"],
            "progress": batch_state["progress"],
            "message": batch_state["message"],
            "started_at": batch_state["started_at"],
            "operation_type": batch_state["operation_type"],
            "total_count": batch_state["total_count"],
            "completed_count": batch_state["completed_count"],
            "failed_count": batch_state["failed_count"],
            "results_summary": _get_batch_results_summary(batch_state)
        },
        request_id=request_id
    )


@router.get("/batch/{batch_id}/results", response_model=ApiResponse)
@limiter.limit("20/minute")
async def get_batch_results(
    request: Request,
    batch_id: str,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Get detailed results from a batch operation."""
    if batch_id not in batch_operations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch operation not found"
        )

    batch_state = batch_operations[batch_id]

    # Check access
    if (batch_state["user_id"] != current_user["user_id"] and
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this batch operation"
        )

    return ApiResponse(
        success=True,
        message="Batch operation results retrieved",
        data={
            "batch_id": batch_id,
            "status": batch_state["status"],
            "operation_type": batch_state["operation_type"],
            "results": batch_state["results"],
            "summary": {
                "total_repositories": batch_state["total_count"],
                "completed": batch_state["completed_count"],
                "failed": batch_state["failed_count"],
                "success_rate": batch_state["completed_count"] / batch_state["total_count"] if batch_state["total_count"] > 0 else 0
            }
        },
        request_id=request_id
    )


# Background Functions

async def perform_export_operation(
    export_id: str,
    export_request: ExportRequest,
    user_id: str
) -> None:
    """Perform export operation in background."""
    try:
        export_state = active_exports[export_id]
        export_state["status"] = "running"
        export_state["message"] = "Starting export..."
        export_state["progress"] = 0.1

        # Create export manager
        export_manager = ExportManager()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if export_request.filename:
            filename = export_request.filename
        else:
            filename = f"githound_export_{export_request.export_type}_{timestamp}.{export_request.format.value}"

        # Create output path
        output_path = Path("/tmp") / filename

        export_state["message"] = "Generating export data..."
        export_state["progress"] = 0.3

        # Perform export based on type
        if export_request.export_type == "repository_metadata":
            await _export_repository_metadata(export_request, export_manager, output_path)
        elif export_request.export_type == "search_results":
            await _export_search_results(export_request, export_manager, output_path)
        elif export_request.export_type == "analysis_report":
            await _export_analysis_report(export_request, export_manager, output_path)
        else:
            raise ValueError(f"Unknown export type: {export_request.export_type}")

        # Complete export
        export_state["status"] = "completed"
        export_state["message"] = "Export completed successfully"
        export_state["progress"] = 1.0
        export_state["file_path"] = str(output_path)
        export_state["filename"] = filename
        export_state["download_url"] = f"/api/v3/integration/export/{export_id}/download"

    except Exception as e:
        export_state = active_exports[export_id]
        export_state["status"] = "failed"
        export_state["message"] = f"Export failed: {str(e)}"
        export_state["error"] = str(e)


async def perform_batch_operation(
    batch_id: str,
    batch_request: BatchOperationRequest,
    user_id: str
) -> None:
    """Perform batch operation in background."""
    try:
        batch_state = batch_operations[batch_id]
        batch_state["status"] = "running"
        batch_state["message"] = "Starting batch operation..."
        batch_state["progress"] = 0.1

        if batch_request.parallel:
            # Execute operations in parallel
            semaphore = asyncio.Semaphore(batch_request.max_concurrent)
            tasks: list[Any] = []

            for repo_path in batch_request.repositories:
                task = _execute_single_operation(
                    semaphore,
                    batch_id,
                    batch_request.operation_type,
                    repo_path,
                    batch_request.parameters
                )
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Execute operations sequentially
            for i, repo_path in enumerate(batch_request.repositories):
                await _execute_single_operation(
                    None,
                    batch_id,
                    batch_request.operation_type,
                    repo_path,
                    batch_request.parameters
                )

                # Update progress
                progress = (i + 1) / len(batch_request.repositories)
                batch_state["progress"] = progress

        # Complete batch operation
        batch_state["status"] = "completed"
        batch_state["message"] = f"Batch operation completed: {batch_state['completed_count']} successful, {batch_state['failed_count']} failed"
        batch_state["progress"] = 1.0

    except Exception as e:
        batch_state = batch_operations[batch_id]
        batch_state["status"] = "failed"
        batch_state["message"] = f"Batch operation failed: {str(e)}"
        batch_state["error"] = str(e)


# Helper Functions

def _get_batch_results_summary(batch_state: Dict[str, Any]) -> Dict[str, Any]:
    """Get summary of batch operation results."""
    results = batch_state.get("results", {})

    successful = [repo for repo, result in results.items() if result.get("status") == "success"]
    failed = [repo for repo, result in results.items() if result.get("status") == "error"]

    return {
        "successful_repositories": successful[:5],  # Show first 5
        "failed_repositories": failed[:5],  # Show first 5
        "total_successful": len(successful),
        "total_failed": len(failed)
    }


async def _execute_single_operation(
    semaphore: Optional[asyncio.Semaphore],
    batch_id: str,
    operation_type: str,
    repo_path: str,
    parameters: Dict[str, Any]
) -> None:
    """Execute a single operation in a batch."""
    if semaphore:
        async with semaphore:
            await _perform_single_operation(batch_id, operation_type, repo_path, parameters)
    else:
        await _perform_single_operation(batch_id, operation_type, repo_path, parameters)


async def _perform_single_operation(
    batch_id: str,
    operation_type: str,
    repo_path: str,
    parameters: Dict[str, Any]
) -> None:
    """Perform a single operation on a repository."""
    try:
        batch_state = batch_operations[batch_id]

        # Simulate operation based on type
        if operation_type == "status_check":
            # Repository status check
            from .git_operations import GitOperationsManager
            git_ops = GitOperationsManager()
            result = git_ops.get_repository_status(repo_path)

        elif operation_type == "branch_list":
            # List branches
            from .git_operations import GitOperationsManager
            git_ops = GitOperationsManager()
            result = git_ops.list_branches(repo_path)

        else:
            result = {"message": f"Operation {operation_type} not implemented"}

        # Store result
        batch_state["results"][repo_path] = {
            "status": "success",
            "data": result,
            "completed_at": datetime.now()
        }
        batch_state["completed_count"] += 1

    except Exception as e:
        batch_state = batch_operations[batch_id]
        batch_state["results"][repo_path] = {
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now()
        }
        batch_state["failed_count"] += 1


async def _export_repository_metadata(
    export_request: ExportRequest,
    export_manager: ExportManager,
    output_path: Path
) -> None:
    """Export repository metadata."""
    # Implementation would go here
    pass


async def _export_search_results(
    export_request: ExportRequest,
    export_manager: ExportManager,
    output_path: Path
) -> None:
    """Export search results."""
    # Implementation would go here
    pass


async def _export_analysis_report(
    export_request: ExportRequest,
    export_manager: ExportManager,
    output_path: Path
) -> None:
    """Export analysis report."""
    # Implementation would go here
    pass
