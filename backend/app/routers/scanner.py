"""
API routes for controlling the Raspberry Pi Camera barcode scanner.

This file provides endpoints so the touch screen can check if the camera is
active, display a live camera preview box, check for newly scanned items, and
start or stop the camera.
"""

import asyncio
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.services.inventory.inventory import inventory_service
from app.services.scanner.scanner import get_barcode_scanner

router = APIRouter(prefix="/scanner", tags=["Hardware Scanner"])


@router.get("/status")
def get_scanner_status():
    """Tells the frontend whether the physical camera scanner is currently running and its frame/decode rates."""
    scanner = get_barcode_scanner()
    return {
        "running": scanner.is_running,
        "sensor": "Raspberry Pi Camera Module v3 (PDAF autofocus)",
        "preview_fps": getattr(scanner, "fps", 12),
        "scan_interval_seconds": getattr(scanner, "scan_interval_seconds", 0.75),
    }


@router.get("/preview")
async def get_scanner_preview(request: Request):
    """
    Streams live video frames from the camera to the Scan Modal so the user can
    easily aim the product barcode in front of the lens.
    """
    scanner = get_barcode_scanner()

    async def frame_generator():
        while True:
            if await request.is_disconnected():
                break
            jpeg = scanner.get_latest_jpeg()
            if jpeg:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )
            stream_interval = 1.0 / max(1, getattr(scanner, "fps", 12))
            await asyncio.sleep(stream_interval)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/frame")
def get_scanner_frame():
    """Returns a single recent camera picture as a JPEG image."""
    scanner = get_barcode_scanner()
    jpeg = scanner.get_latest_jpeg()
    if not jpeg:
        raise HTTPException(status_code=503, detail="Camera frame not ready")
    return Response(
        content=jpeg,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/latest-event")
def get_latest_scan_event():
    """
    Returns the most recent item scanned by the physical camera.
    The frontend checks this every second to show the 'Added to Stock' pop-up.
    """
    return inventory_service.latest_scan_event


@router.post("/start")
def start_camera_scanner():
    """Turns on the background camera barcode scanner."""
    scanner = get_barcode_scanner()
    if not scanner.is_running:
        scanner.start(inventory_service.handle_hardware_scan)
        return {"status": "started", "message": "Picamera2 barcode scanner loop is running."}
    return {"status": "already_running"}


@router.post("/stop")
def stop_camera_scanner():
    """Turns off the background camera barcode scanner and frees the camera."""
    scanner = get_barcode_scanner()
    if scanner.is_running:
        scanner.stop()
        return {"status": "stopped", "message": "Picamera2 camera released."}
    return {"status": "already_stopped"}
