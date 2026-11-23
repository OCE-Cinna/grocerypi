"""
Main services package for GroceryPi.

This folder contains the core logic of the application, separated into clear topics:
- inventory: Handling scanned barcodes and updating kitchen stock.
- nutrition: Adding up calories, protein, carbs, and Nutri-Score for stocked food.
- prediction: Calculating when items will run out and building supermarket lists.
- scanner: Reading barcodes from the Raspberry Pi Camera Module v3.
"""

from app.services.inventory import InventoryService, inventory_service
from app.services.nutrition import NutritionService, nutrition_service
from app.services.prediction import (
    PredictionEngine,
    get_cart_replenishment_suggestions,
    prediction_engine,
)
from app.services.scanner import (
    IBarcodeScanner,
    MockBarcodeScanner,
    Picamera2BarcodeScanner,
    get_barcode_scanner,
)

__all__ = [
    "InventoryService",
    "inventory_service",
    "NutritionService",
    "nutrition_service",
    "PredictionEngine",
    "prediction_engine",
    "get_cart_replenishment_suggestions",
    "IBarcodeScanner",
    "Picamera2BarcodeScanner",
    "MockBarcodeScanner",
    "get_barcode_scanner",
]
