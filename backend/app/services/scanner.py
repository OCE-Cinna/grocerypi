import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Tuple
import cv2
import numpy as np

try:
    from pyzbar import pyzbar
    _HAS_PYZBAR = True
except ImportError:
    _HAS_PYZBAR = False

logger = logging.getLogger("grocerypi.scanner")


class IBarcodeScanner(ABC):
    """Abstract interface defining the barcode scanning service contract (SOLID ISP / DIP)."""

    @abstractmethod
    def start(self, on_scan: Callable[[str], None]) -> None:
        """Start the background optical capture and barcode detection stream."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the capture loop and release camera hardware resources."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Returns True if the optical scanner loop is currently active."""
        pass

    @abstractmethod
    def decode_frame(self, frame: np.ndarray) -> Optional[str]:
        """Decode a single numpy image frame and return the detected barcode string."""
        pass


class Picamera2BarcodeScanner(IBarcodeScanner):
    """
    Physical hardware barcode scanner implementation for Raspberry Pi Camera Module v3.
    Utilizes picamera2 for frame capture with PDAF autofocus and OpenCV BarcodeDetector.
    """

    def __init__(
        self,
        resolution: Tuple[int, int] = (1280, 720),
        debounce_seconds: float = 2.5,
        fps: int = 15,
    ):
        self.resolution = resolution
        self.debounce_seconds = debounce_seconds
        self.fps = fps
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._on_scan_callback: Optional[Callable[[str], None]] = None
        self._recent_scans: Dict[str, float] = {}  # {barcode: timestamp}
        self._detector = cv2.barcode.BarcodeDetector()
        self._picam2 = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def decode_frame(self, frame: np.ndarray) -> Optional[str]:
        """
        Attempts to detect and decode an EAN-13, UPC, or 1D/2D barcode from a frame.
        Applies a high-performance dual-engine pipeline:
          1. pyzbar (highest recognition rate & angle tolerance for 1D grocery packaging)
          2. cv2.barcode.BarcodeDetector (OpenCV fallback)
          3. Contrast / Gaussian smoothing fallback for high-gloss kitchen reflections
        """
        if frame is None or frame.size == 0:
            return None

        # Convert to grayscale if frame is in RGB/BGR
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Primary: pyzbar (standard retail 1D/2D decoder)
        if _HAS_PYZBAR:
            try:
                results = pyzbar.decode(gray)
                for item in results:
                    code = item.data.decode("utf-8", errors="ignore").strip()
                    if code:
                        return code
            except Exception as e:
                logger.debug(f"pyzbar decode pass error: {e}")

        # Secondary: OpenCV BarcodeDetector
        try:
            retval, decoded_info, decoded_type, points = self._detector.detectAndDecode(gray)
            if retval and decoded_info:
                for item in decoded_info:
                    clean_code = str(item).strip()
                    if clean_code:
                        return clean_code
        except Exception:
            pass

        # Fallback: Mild Gaussian blur for packaging glare/reflections
        if _HAS_PYZBAR:
            try:
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                results = pyzbar.decode(blurred)
                for item in results:
                    code = item.data.decode("utf-8", errors="ignore").strip()
                    if code:
                        return code
            except Exception:
                pass

        return None

    def _should_debounce(self, barcode: str) -> bool:
        """Returns True if the barcode was already processed within the cooldown window."""
        now = time.time()
        last_seen = self._recent_scans.get(barcode, 0.0)
        
        # Clean up stale entries older than 30 seconds
        stale_keys = [k for k, v in self._recent_scans.items() if now - v > 30.0]
        for k in stale_keys:
            del self._recent_scans[k]

        if now - last_seen < self.debounce_seconds:
            return True

        self._recent_scans[barcode] = now
        return False

    def _capture_loop(self) -> None:
        """Continuous camera frame reading thread."""
        logger.info("Initializing Picamera2 for barcode scanner...")
        try:
            import picamera2
            self._picam2 = picamera2.Picamera2()

            # Configure Camera Module v3 preview/capture stream
            config = self._picam2.create_video_configuration(
                main={"size": self.resolution, "format": "RGB888"}
            )
            self._picam2.configure(config)
            
            # Start camera hardware
            self._picam2.start()

            # Set Continuous Autofocus (AfMode = 2) for Camera Module v3 PDAF
            try:
                self._picam2.set_controls({"AfMode": 2})
                logger.info("Camera Module v3 Continuous Autofocus (PDAF) engaged.")
            except Exception as af_err:
                logger.warning(f"Continuous autofocus configuration notice: {af_err}")

            logger.info("Picamera2 capture loop started successfully.")
            interval = 1.0 / self.fps

            while self._is_running:
                start_time = time.time()
                
                # Capture frame as numpy array
                frame = self._picam2.capture_array("main")
                
                barcode = self.decode_frame(frame)
                if barcode:
                    if not self._should_debounce(barcode):
                        logger.info(f"Barcode detected: {barcode}")
                        if self._on_scan_callback:
                            try:
                                self._on_scan_callback(barcode)
                            except Exception as cb_err:
                                logger.error(f"Error in on_scan callback: {cb_err}")
                    else:
                        logger.debug(f"Debounced barcode: {barcode}")

                # Rate limiting to target FPS
                elapsed = time.time() - start_time
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Fatal error in Picamera2 capture loop: {e}", exc_info=True)
        finally:
            self._cleanup_camera()
            self._is_running = False
            logger.info("Picamera2 capture loop stopped.")

    def _cleanup_camera(self) -> None:
        """Safely stops and closes the picamera2 instance."""
        if self._picam2:
            try:
                self._picam2.stop()
            except Exception:
                pass
            try:
                self._picam2.close()
            except Exception:
                pass
            self._picam2 = None

    def start(self, on_scan: Callable[[str], None]) -> None:
        """Start the background scanner thread."""
        if self._is_running:
            logger.warning("Barcode scanner is already running.")
            return

        self._on_scan_callback = on_scan
        self._is_running = True
        self._thread = threading.Thread(target=self._capture_loop, name="Picamera2ScannerThread", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background scanner thread."""
        if not self._is_running:
            return

        logger.info("Stopping Picamera2 barcode scanner...")
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._cleanup_camera()


class MockBarcodeScanner(IBarcodeScanner):
    """Mock scanner used for unit testing, CI pipelines, or development without camera hardware."""

    def __init__(self, debounce_seconds: float = 2.0):
        self.debounce_seconds = debounce_seconds
        self._is_running = False
        self._on_scan_callback: Optional[Callable[[str], None]] = None
        self._recent_scans: Dict[str, float] = {}

    @property
    def is_running(self) -> bool:
        return self._is_running

    def decode_frame(self, frame: np.ndarray) -> Optional[str]:
        return None

    def simulate_scan(self, barcode: str) -> bool:
        """Inject a simulated barcode scan."""
        if not self._is_running:
            logger.warning("Mock scanner is not running, scan ignored.")
            return False

        now = time.time()
        last_seen = self._recent_scans.get(barcode, 0.0)
        if now - last_seen < self.debounce_seconds:
            logger.debug(f"Mock scanner debounced: {barcode}")
            return False

        self._recent_scans[barcode] = now
        if self._on_scan_callback:
            self._on_scan_callback(barcode)
        return True

    def start(self, on_scan: Callable[[str], None]) -> None:
        self._on_scan_callback = on_scan
        self._is_running = True
        logger.info("Mock barcode scanner started.")

    def stop(self) -> None:
        self._is_running = False
        logger.info("Mock barcode scanner stopped.")


# Singleton / Factory accessor
_scanner_instance: Optional[IBarcodeScanner] = None

def get_barcode_scanner(use_mock: bool = False) -> IBarcodeScanner:
    """Provides a singleton instance of the barcode scanner service."""
    global _scanner_instance
    if _scanner_instance is None:
        if use_mock:
            _scanner_instance = MockBarcodeScanner()
        else:
            try:
                _scanner_instance = Picamera2BarcodeScanner()
            except Exception as e:
                logger.warning(f"Could not initialize physical camera scanner ({e}). Falling back to Mock.")
                _scanner_instance = MockBarcodeScanner()
    return _scanner_instance

