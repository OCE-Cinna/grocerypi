"""
Main starting point for the GroceryPi backend server.

This file starts the FastAPI web server, sets up permissions so the touch screen
can talk to the backend, starts the camera scanner in the background when the
system turns on, and connects all the different API routes.
"""

from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, cart, inventory, products, scanner, system
from app.services.inventory.inventory import inventory_service
from app.services.scanner.scanner import get_barcode_scanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grocerypi.main")

# Create all database tables if they do not exist yet
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs automatically when the backend starts up and shuts down.
    It turns on the physical camera barcode scanner on startup and safely turns
    it off when the server closes.
    """
    auto_start = os.getenv("ENABLE_HARDWARE_SCANNER", "true").lower() in ("true", "1", "yes")
    scanner_service = get_barcode_scanner()

    if auto_start:
        logger.info("Starting background hardware barcode scanner on boot...")
        scanner_service.start(inventory_service.handle_hardware_scan)

    yield

    if scanner_service.is_running:
        logger.info("Stopping hardware barcode scanner on server shutdown...")
        scanner_service.stop()


# Create the main FastAPI application
app = FastAPI(
    title="GroceryPi API",
    description="Smart kitchen inventory and grocery kiosk API running on a Raspberry Pi.",
    version="2.0.0",
    lifespan=lifespan,
)

# Allow the React frontend screen to make requests to this backend server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect all route groups (inventory, products, cart, camera scanner, system, and login)
app.include_router(inventory.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(scanner.router)
app.include_router(system.router)
app.include_router(auth.router)


@app.get("/", tags=["Health"])
def health_check():
    """Simple check to confirm that the backend server is online and working."""
    return {
        "status": "ok",
        "service": "GroceryPi API",
        "version": "2.0.0",
        "paradigm": "Items IN (Inventory Prediction)",
    }
