"""
Package for the Camera Barcode Scanner Service.

Exports the common scanner interface (IBarcodeScanner), the physical Raspberry Pi
camera scanner (Picamera2BarcodeScanner), the test scanner (MockBarcodeScanner),
and the helper function to get the active scanner.
"""

from app.services.scanner.scanner import (
    IBarcodeScanner,
    MockBarcodeScanner,
    Picamera2BarcodeScanner,
    get_barcode_scanner,
)

__all__ = [
    "IBarcodeScanner",
    "Picamera2BarcodeScanner",
    "MockBarcodeScanner",
    "get_barcode_scanner",
]
