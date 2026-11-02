import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal, get_db
from app.routers import auth, lists, items, inventory, products
from app.services.scanner import get_barcode_scanner
from app.models import ProductCatalog, InventoryItem, ScanLog, InventoryStatus, ScanStatus
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grocerypi.main")

# Auto-create all tables
Base.metadata.create_all(bind=engine)


def handle_hardware_scan(barcode: str):
    """Callback invoked by the physical Picamera2 scanner thread upon detecting a barcode."""
    logger.info(f"[HARDWARE SCANNER EVENT] Ingesting detected barcode: {barcode}")
    db: Session = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        product = db.query(ProductCatalog).filter(ProductCatalog.barcode == barcode.strip()).first()
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
            logger.info(f"[HARDWARE SCANNER] Added '{product.name}' to inventory (+1). Total: {inv.quantity}")
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
    except Exception as e:
        db.rollback()
        logger.error(f"[HARDWARE SCANNER] Error handling barcode {barcode}: {e}", exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI and the background hardware scanner."""
    auto_start = os.getenv("ENABLE_HARDWARE_SCANNER", "false").lower() in ("true", "1", "yes")
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


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "GroceryPi API",
        "version": "2.0.0",
        "paradigm": "Items IN (Inventory Prediction)",
    }
