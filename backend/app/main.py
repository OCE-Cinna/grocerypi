import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal, get_db
from app.routers import auth, lists, items, inventory, products
from app.services.scanner import get_barcode_scanner
from app.services.ah_client import resolve_barcode_to_catalog_item
from app.models import ProductCatalog, InventoryItem, ScanLog, InventoryStatus, ScanStatus
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grocerypi.main")

# Auto-create all tables
Base.metadata.create_all(bind=engine)

_latest_scan_event = {
    "scan_id": 0,
    "scan_status": None,
    "barcode": None,
    "product": None,
    "inventory_item": None,
    "timestamp": None,
    "message": None,
}


def handle_hardware_scan(barcode: str):
    """Callback invoked by the physical Picamera2 scanner thread upon detecting a barcode."""
    global _latest_scan_event
    logger.info(f"[HARDWARE SCANNER EVENT] Ingesting detected barcode: {barcode}")
    db: Session = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        clean_code = barcode.strip()
        product = db.query(ProductCatalog).filter(ProductCatalog.barcode == clean_code).first()
        if not product:
            try:
                product = resolve_barcode_to_catalog_item(clean_code, db)
            except Exception as res_err:
                logger.error(f"[HARDWARE SCANNER] Failed to resolve barcode '{clean_code}' from AH API: {res_err}")

        if product:
            inv = db.query(InventoryItem).filter(InventoryItem.product_id == product.id).first()
            if inv:
                inv.quantity += 1
                inv.last_restocked_at = now_utc
                inv.status = InventoryStatus.IN_STOCK
            else:
                inv = InventoryItem(
                    product_id=product.id,
                    quantity=1,
                    status=InventoryStatus.IN_STOCK,
                    last_restocked_at=now_utc,
                )
                db.add(inv)

            log_entry = ScanLog(
                raw_barcode=barcode,
                product_id=product.id,
                status=ScanStatus.SUCCESS,
                device_info="Raspberry Pi Camera v3 (Hardware Loop)",
                scanned_at=now_utc,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(inv)
            logger.info(f"[HARDWARE SCANNER] Added '{product.name}' to inventory (+1). Total: {inv.quantity}")

            _latest_scan_event = {
                "scan_id": int(now_utc.timestamp() * 1000),
                "scan_status": "SUCCESS",
                "barcode": barcode,
                "device_info": "Raspberry Pi Camera Module v3 (Optical Loop)",
                "product": {
                    "id": product.id,
                    "barcode": product.barcode,
                    "name": product.name,
                    "brand": product.brand,
                    "package_size": product.package_size,
                    "category": product.category.value if hasattr(product.category, "value") else str(product.category),
                    "nutriscore": product.nutriscore,
                    "is_vegan": product.is_vegan,
                    "is_vegetarian": product.is_vegetarian,
                },
                "inventory_item": {
                    "id": inv.id,
                    "product_id": inv.product_id,
                    "quantity": inv.quantity,
                    "status": inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                },
                "timestamp": now_utc.isoformat(),
                "message": f"Added '{product.name}' (+1)",
            }
        else:
            log_entry = ScanLog(
                raw_barcode=barcode,
                product_id=None,
                status=ScanStatus.UNKNOWN_BARCODE,
                device_info="Raspberry Pi Camera v3 (Hardware Loop)",
                scanned_at=now_utc,
            )
            db.add(log_entry)
            db.commit()
            logger.warning(f"[HARDWARE SCANNER] Unknown barcode: '{barcode}'")

            _latest_scan_event = {
                "scan_id": int(now_utc.timestamp() * 1000),
                "scan_status": "UNKNOWN_BARCODE",
                "barcode": barcode,
                "product": None,
                "inventory_item": None,
                "timestamp": now_utc.isoformat(),
                "message": f"Barcode '{barcode}' not found in catalog.",
            }
    except Exception as e:
        db.rollback()
        logger.error(f"[HARDWARE SCANNER] Error handling barcode {barcode}: {e}", exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI and the background hardware scanner."""
    auto_start = os.getenv("ENABLE_HARDWARE_SCANNER", "true").lower() in ("true", "1", "yes")
    scanner = get_barcode_scanner()

    if auto_start:
        logger.info("Starting background hardware barcode scanner on boot...")
        scanner.start(handle_hardware_scan)

    yield

    if scanner.is_running:
        logger.info("Stopping hardware barcode scanner on server shutdown...")
        scanner.stop()


app = FastAPI(
    title="GroceryPi API",
    description="Smart kitchen inventory & grocery kiosk API — running on Raspberry Pi.",
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(inventory.router)
app.include_router(products.router)
app.include_router(auth.router)
app.include_router(lists.router)
app.include_router(items.router)


# ─── Hardware Scanner Control Endpoints ───────────────────────────────────────

@app.get("/scanner/status", tags=["Hardware Scanner"])
def get_scanner_status():
    """Checks whether the physical camera scanner background loop is running."""
    scanner = get_barcode_scanner()
    return {"running": scanner.is_running, "sensor": "Raspberry Pi Camera Module v3 (PDAF autofocus)"}


@app.get("/scanner/preview", tags=["Hardware Scanner"])
async def get_scanner_preview(request: Request):
    """MJPEG streaming endpoint for live camera framing & viewfinder preview."""
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
            await asyncio.sleep(0.05)  # 20 FPS smooth refresh rate

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )


@app.get("/scanner/frame", tags=["Hardware Scanner"])
def get_scanner_frame():
    """Returns a single latest snapshot frame (useful for fast polling or frame refreshes)."""
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
        }
    )


@app.get("/scanner/latest-event", tags=["Hardware Scanner"])
def get_latest_scan_event():
    """Returns the most recent barcode scan event detected by the hardware scanner loop."""
    return _latest_scan_event


@app.post("/scanner/start", tags=["Hardware Scanner"])
def start_camera_scanner():
    """Starts the physical Picamera2 optical scanning thread."""
    scanner = get_barcode_scanner()
    if not scanner.is_running:
        scanner.start(handle_hardware_scan)
        return {"status": "started", "message": "Picamera2 barcode scanner loop is running."}
    return {"status": "already_running"}


@app.post("/scanner/stop", tags=["Hardware Scanner"])
def stop_camera_scanner():
    """Stops the physical optical scanning loop and frees camera hardware."""
    scanner = get_barcode_scanner()
    if scanner.is_running:
        scanner.stop()
        return {"status": "stopped", "message": "Picamera2 camera released."}
    return {"status": "already_stopped"}


@app.post("/system/exit-kiosk", tags=["System"])
def exit_kiosk():
    """Terminates the Chromium kiosk browser to return to Raspberry Pi OS desktop."""
    logger.info("Exit kiosk requested via Home button.")
    import subprocess
    try:
        subprocess.Popen(
            ["sh", "-c", "pkill -f 'chromium.*--kiosk' || pkill -f 'chromium-browser.*--kiosk' || pkill -f 'chromium'"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "ok", "message": "Closing kiosk mode..."}
    except Exception as e:
        logger.error(f"Error terminating kiosk: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "GroceryPi API",
        "version": "2.0.0",
        "paradigm": "Items IN (Inventory Prediction)",
    }
