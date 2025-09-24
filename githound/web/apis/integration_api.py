"""
Integration API endpoints for GitHound.

Provides export capabilities, webhook management, batch operations,
and other integration features.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ...models import OutputFormat
from ..middleware.rate_limiting import get_limiter
from ..models.api_models import ApiResponse, ExportRequest, ExportResponse
from ..services.auth_service import require_admin, require_user
from ..services.webhook_service import WebhookEndpoint, webhook_manager
from ..utils.validation import get_request_id, validate_repo_path

# Create router
router = APIRouter(prefix="/api/integration", tags=["integration"])
limiter = get_limiter()


# Export Models
class BatchExportRequest(BaseModel):
    """Request for batch export operations."""

    search_ids: list[str] = Field(..., description="List of search IDs")
    format: OutputFormat = Field(..., description="Export format")
    include_metadata: bool = Field(True, description="Include metadata")
    merge_results: bool = Field(False, description="Merge all results into one file")


class WebhookCreateRequest(BaseModel):
    """Request for webhook creation."""

    url: str = Field(..., description="Webhook URL")
    secret: str | None = Field(None, description="Webhook secret")
    events: list[str] = Field(..., description="Events to subscribe to")
    active: bool = Field(True, description="Whether webhook is active")


class WebhookUpdateRequest(BaseModel):
    """Request for webhook updates."""

    url: str | None = Field(None, description="Webhook URL")
    secret: str | None = Field(None, description="Webhook secret")
    events: list[str] | None = Field(None, description="Events to subscribe to")
    active: bool | None = Field(None, description="Whether webhook is active")


# Export Endpoints


@router.post("/export", response_model=ExportResponse)
@limiter.limit("3/minute")
async def export_search_results(
    request: Request,
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ExportResponse:
    """
    Export search results to various formats.

    Supports JSON, CSV, and other formats. Large exports are processed
    in the background.
    """
    try:
        export_id = str(uuid.uuid4())

        # Start background export task
        background_tasks.add_task(
            _process_export, export_id, export_request, current_user["user_id"]
        )

        filename = (
            export_request.filename
            or f"search_results_{export_request.search_id}.{export_request.format.value}"
        )

        return ExportResponse(
            export_id=export_id,
            status="processing",
            download_url=None,  # Will be set when processing completes
            filename=filename,
            file_size=None,  # Will be set when processing completes
            format=export_request.format,
            created_at=datetime.now(),
            expires_at=None,  # Will be set when processing completes
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start export: {str(e)}",
        )


@router.post("/export/batch", response_model=ExportResponse)
@limiter.limit("1/minute")
async def batch_export_search_results(
    request: Request,
    batch_request: BatchExportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id),
) -> ExportResponse:
    """
    Export multiple search results in batch.

    Combines multiple search results into a single export file.
    Requires admin privileges.
    """
    try:
        export_id = str(uuid.uuid4())

        # Start background batch export task
        background_tasks.add_task(
            _process_batch_export, export_id, batch_request, current_user["user_id"]
        )

        filename = (
            f"batch_export_{len(batch_request.search_ids)}_searches.{batch_request.format.value}"
        )

        return ExportResponse(
            export_id=export_id,
            status="processing",
            download_url=None,  # Will be set when processing completes
            filename=filename,
            file_size=None,  # Will be set when processing completes
            format=batch_request.format,
            created_at=datetime.now(),
            expires_at=None,  # Will be set when processing completes
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch export: {str(e)}",
        )


@router.get("/export/{export_id}/status", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_export_status(
    request: Request,
    export_id: str,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Get the status of an export operation.

    Returns current status, progress, and download information.
    """
    try:
        # This would integrate with the actual export tracking system
        status_info = {
            "export_id": export_id,
            "status": "completed",  # This would be dynamic
            "progress": 100.0,
            "download_url": f"/api/integration/export/{export_id}/download",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }

        return ApiResponse(
            success=True, message="Export status retrieved", data=status_info, request_id=request_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export status: {str(e)}",
        )


@router.get("/export/{export_id}/download")
@limiter.limit("10/minute")
async def download_export(
    request: Request, export_id: str, current_user: dict[str, Any] = Depends(require_user)
) -> FileResponse:
    """
    Download an exported file.

    Returns the exported file for download.
    """
    try:
        # This would integrate with the actual export storage system
        file_path = Path(f"/tmp/exports/{export_id}.json")  # Example path

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found"
            )

        return FileResponse(
            path=str(file_path), filename=f"export_{export_id}.json", media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download export: {str(e)}",
        )


# Webhook Endpoints


@router.post("/webhooks", response_model=ApiResponse)
@limiter.limit("10/minute")
async def create_webhook(
    request: Request,
    webhook_request: WebhookCreateRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Create a new webhook endpoint.

    Registers a webhook URL to receive event notifications.
    Requires admin privileges.
    """
    try:
        webhook_id = str(uuid.uuid4())

        webhook = WebhookEndpoint(
            id=webhook_id,
            url=webhook_request.url,
            secret=webhook_request.secret,
            events=webhook_request.events,
            active=webhook_request.active,
            last_delivery=None,
            failure_count=0,
            max_failures=5,
        )

        webhook_manager.add_endpoint(webhook)

        return ApiResponse(
            success=True,
            message="Webhook created successfully",
            data={
                "webhook_id": webhook_id,
                "url": webhook_request.url,
                "events": webhook_request.events,
                "active": webhook_request.active,
            },
            request_id=request_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook: {str(e)}",
        )


@router.get("/webhooks", response_model=ApiResponse)
@limiter.limit("30/minute")
async def list_webhooks(
    request: Request,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    List all webhook endpoints.

    Returns all registered webhook endpoints.
    Requires admin privileges.
    """
    try:
        webhooks = webhook_manager.list_endpoints()

        webhook_data = []
        for webhook in webhooks:
            webhook_data.append(
                {
                    "id": webhook.id,
                    "url": webhook.url,
                    "events": webhook.events,
                    "active": webhook.active,
                    "created_at": webhook.created_at.isoformat(),
                    "last_delivery": (
                        webhook.last_delivery.isoformat() if webhook.last_delivery else None
                    ),
                    "failure_count": webhook.failure_count,
                }
            )

        return ApiResponse(
            success=True,
            message=f"Retrieved {len(webhook_data)} webhooks",
            data={"webhooks": webhook_data, "total_count": len(webhook_data)},
            request_id=request_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list webhooks: {str(e)}",
        )


@router.put("/webhooks/{webhook_id}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def update_webhook(
    request: Request,
    webhook_id: str,
    webhook_update: WebhookUpdateRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Update a webhook endpoint.

    Updates webhook configuration.
    Requires admin privileges.
    """
    try:
        updates: dict[str, Any] = {}
        if webhook_update.url is not None:
            updates["url"] = webhook_update.url
        if webhook_update.secret is not None:
            updates["secret"] = webhook_update.secret
        if webhook_update.events is not None:
            updates["events"] = webhook_update.events
        if webhook_update.active is not None:
            updates["active"] = webhook_update.active

        success = webhook_manager.update_endpoint(webhook_id, updates)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        return ApiResponse(
            success=True,
            message="Webhook updated successfully",
            data={"webhook_id": webhook_id, "updates": updates},
            request_id=request_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update webhook: {str(e)}",
        )


@router.delete("/webhooks/{webhook_id}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def delete_webhook(
    request: Request,
    webhook_id: str,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Delete a webhook endpoint.

    Removes a webhook endpoint.
    Requires admin privileges.
    """
    try:
        success = webhook_manager.remove_endpoint(webhook_id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        return ApiResponse(
            success=True,
            message="Webhook deleted successfully",
            data={"webhook_id": webhook_id},
            request_id=request_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook: {str(e)}",
        )


# Helper functions


async def _process_export(export_id: str, export_request: ExportRequest, user_id: str) -> None:
    """Process export in background."""
    # This would integrate with the actual export system
    pass


async def _process_batch_export(
    export_id: str, batch_request: BatchExportRequest, user_id: str
) -> None:
    """Process batch export in background."""
    # This would integrate with the actual export system
    pass
