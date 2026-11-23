"""
Camera barcode scanner service for GroceryPi.

This file controls the Raspberry Pi Camera Module v3 to read barcodes from
grocery packages. It captures photos in the background, reads the barcode numbers
using image-reading libraries (pyzbar and OpenCV), prevents the same item from
being scanned twice by mistake within a few seconds, and provides a fake scanner
(MockBarcodeScanner) so the app can also be tested on a normal computer without
a Pi camera attached.
"""

from abc import ABC, abstractmethod
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    cv2 = None  # type: ignore
    np = None  # type: ignore
    _HAS_CV2 = False

try:
    from pyzbar import pyzbar
    _HAS_PYZBAR = True
except ImportError:
    _HAS_PYZBAR = False

logger = logging.getLogger("grocerypi.scanner")


class IBarcodeScanner(ABC):
    """
    Common template that any barcode scanner must follow.
    Because the app uses this template, we can switch between the Pi camera,
    a USB barcode scanner, or a test scanner without changing the rest of the code.
    """

    @abstractmethod
    def start(self, on_scan: Callable[[str], None]) -> None:
        """Turns on the scanner in the background and runs on_scan when a barcode is read."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Turns off the scanner and releases the camera hardware."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Returns True if the scanner is currently active."""
        pass

    @abstractmethod
    def decode_frame(self, frame: Any) -> Optional[str]:
        """Tries to find and read a barcode number from a single camera picture."""
        pass

    @abstractmethod
    def get_latest_jpeg(self) -> Optional[bytes]:
        """Returns the most recent camera image as a JPEG file for the live screen preview."""
        pass


class Picamera2BarcodeScanner(IBarcodeScanner):
    """
    Controls the physical Raspberry Pi Camera Module v3.
    Takes pictures continuously in the background, focuses the lens automatically,
    and checks each image for a product barcode.
    """

    def __init__(
        self,
        resolution: Tuple[int, int] = (1280, 720),
        debounce_seconds: float = 2.5,
        fps: Optional[int] = None,
        vflip: Optional[bool] = None,
        hflip: Optional[bool] = None,
    ):
        """
        Sets up camera settings such as image size, pause time between identical
        scans (debounce_seconds), frames per second (defaults to 1 FPS to keep
        the Raspberry Pi cool), and flipping the image if the camera mount is upside down.
        """
        self.resolution = resolution
        self.debounce_seconds = debounce_seconds
        self.fps = fps if fps is not None else int(os.getenv("CAMERA_FPS", "1"))
        self.vflip = vflip if vflip is not None else os.getenv("CAMERA_VFLIP", "true").lower() in ("true", "1", "yes")
        self.hflip = hflip if hflip is not None else os.getenv("CAMERA_HFLIP", "false").lower() in ("true", "1", "yes")
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._on_scan_callback: Optional[Callable[[str], None]] = None
        self._recent_scans: Dict[str, float] = {}
        self._detector = cv2.barcode.BarcodeDetector() if _HAS_CV2 else None
        self._picam2 = None
        self._lock = threading.Lock()
        self._latest_jpeg: Optional[bytes] = None
        self._is_decoding: bool = False

    @property
    def is_running(self) -> bool:
        """Returns True if the camera loop is currently running."""
        return self._is_running

    def get_latest_jpeg(self) -> Optional[bytes]:
        """
        Returns the latest camera picture for the Scan Modal preview, or a simple
        placeholder image while the camera is still warming up.
        """
        with self._lock:
            if self._latest_jpeg is not None:
                return self._latest_jpeg
        if not _HAS_CV2:
            return None
        img = np.zeros((360, 480, 3), dtype=np.uint8)
        img[:] = (56, 61, 59)
        cv2.rectangle(img, (80, 60), (400, 300), (139, 228, 195), 2)
        cv2.putText(img, "Scanning Target Area", (130, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (247, 244, 242), 1)
        cv2.putText(img, "Initializing Camera Module v3...", (100, 335), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1)
        ret, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 60])
        return buf.tobytes() if ret else None

    def decode_frame(self, frame: Any) -> Optional[str]:
        """
        Looks for a barcode inside a camera picture:
        1. Converts the image to black-and-white for clearer contrast.
        2. Tries reading the barcode with pyzbar (best for grocery packaging).
        3. If not found, tries reading with OpenCV's barcode detector.
        4. If kitchen light glare gets in the way, applies a slight blur and tries once more.
        """
        if not _HAS_CV2 or frame is None or frame.size == 0:
            return None

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        if _HAS_PYZBAR:
            try:
                results = pyzbar.decode(gray)
                for item in results:
                    code = item.data.decode("utf-8", errors="ignore").strip()
                    if code:
                        return code
            except Exception as e:
                logger.debug(f"pyzbar decode pass error: {e}")

        if self._detector is not None:
            try:
                retval, decoded_info, decoded_type, points = self._detector.detectAndDecode(gray)
                if retval and decoded_info:
                    for item in decoded_info:
                        clean_code = str(item).strip()
                        if clean_code:
                            return clean_code
            except Exception:
                pass

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
        """
        Checks if this exact barcode was already scanned within the last 2.5 seconds.
        This stops the camera from adding the same item multiple times while the user
        is still holding it in front of the lens.
        """
        now = time.time()
        last_seen = self._recent_scans.get(barcode, 0.0)

        stale_keys = [k for k, v in self._recent_scans.items() if now - v > 30.0]
        for k in stale_keys:
            del self._recent_scans[k]

        if now - last_seen < self.debounce_seconds:
            return True

        self._recent_scans[barcode] = now
        return False

    def _capture_loop(self) -> None:
        """
        Runs continuously in the background while the camera is turned on.
        Captures a picture, saves a small version for the live screen preview,
        and checks the picture for a barcode.
        """
        logger.info("Initializing Picamera2 for barcode scanner...")
        try:
            import picamera2
            self._picam2 = picamera2.Picamera2()

            transform = picamera2.libcamera.Transform(
                vflip=1 if self.vflip else 0,
                hflip=1 if self.hflip else 0,
            )
            config = self._picam2.create_video_configuration(
                main={"size": self.resolution, "format": "RGB888"},
                transform=transform,
            )
            self._picam2.configure(config)
            logger.info(f"Picamera2 initialized with hardware transform: vflip={self.vflip}, hflip={self.hflip}")

            self._picam2.start()

            try:
                self._picam2.set_controls({"AfMode": 2})
                logger.info("Camera Module v3 Continuous Autofocus (PDAF) engaged.")
            except Exception as af_err:
                logger.warning(f"Continuous autofocus configuration notice: {af_err}")

            logger.info(f"Picamera2 capture loop started successfully at {self.fps} FPS.")
            interval = 1.0 / max(1, self.fps)

            while self._is_running:
                start_time = time.time()

                try:
                    frame = self._picam2.capture_array("main")
                except Exception as cap_err:
                    logger.warning(f"Frame capture error: {cap_err}")
                    time.sleep(0.1)
                    continue

                if frame is None or frame.size == 0:
                    time.sleep(0.05)
                    continue

                if _HAS_CV2:
                    try:
                        small_frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR)
                        ret, buf = cv2.imencode(".jpg", small_frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
                        if ret:
                            with self._lock:
                                self._latest_jpeg = buf.tobytes()
                    except Exception:
                        pass

                if not self._is_decoding:
                    self._is_decoding = True
                    threading.Thread(
                        target=self._async_decode,
                        args=(frame.copy(),),
                        daemon=True,
                    ).start()

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

    def _async_decode(self, frame: Any) -> None:
        """
        Reads the barcode from a picture in a separate background task so the
        live camera video on the screen stays smooth.
        """
        try:
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
        except Exception as e:
            logger.debug(f"Async barcode decode pass notice: {e}")
        finally:
            self._is_decoding = False

    def _cleanup_camera(self) -> None:
        """Safely closes the connection to the physical Raspberry Pi camera."""
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
        """Starts the background camera thread and links the function to call on each scan."""
        if self._is_running:
            logger.warning("Barcode scanner is already running.")
            return

        self._on_scan_callback = on_scan
        self._is_running = True
        self._thread = threading.Thread(target=self._capture_loop, name="Picamera2ScannerThread", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the background camera thread and frees the camera."""
        if not self._is_running:
            return

        logger.info("Stopping Picamera2 barcode scanner...")
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._cleanup_camera()


class MockBarcodeScanner(IBarcodeScanner):
    """
    Fake barcode scanner used for automated testing or when working on a laptop
    without a physical Raspberry Pi camera attached.
    """

    def __init__(self, debounce_seconds: float = 2.0):
        """Sets up the test scanner with a short cooldown between identical scans."""
        self.debounce_seconds = debounce_seconds
        self._is_running = False
        self._on_scan_callback: Optional[Callable[[str], None]] = None
        self._recent_scans: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._latest_jpeg: Optional[bytes] = None

    @property
    def is_running(self) -> bool:
        """Returns True if the test scanner is turned on."""
        return self._is_running

    def get_latest_jpeg(self) -> Optional[bytes]:
        """Returns a simple placeholder preview image when running in test mode."""
        with self._lock:
            if self._latest_jpeg is not None:
                return self._latest_jpeg
        if not _HAS_CV2:
            return None
        img = np.zeros((360, 480, 3), dtype=np.uint8)
        img[:] = (56, 61, 59)
        cv2.rectangle(img, (80, 60), (400, 300), (139, 228, 195), 2)
        cv2.putText(img, "Scanning Target Area", (130, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (247, 244, 242), 1)
        cv2.putText(img, "Initializing Camera Module v3...", (100, 335), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1)
        ret, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 60])
        return buf.tobytes() if ret else None

    def decode_frame(self, frame: Any) -> Optional[str]:
        """Returns None because the test scanner uses simulate_scan() instead of real photos."""
        return None

    def simulate_scan(self, barcode: str) -> bool:
        """Pretends a barcode was just scanned by the camera (used in automated tests)."""
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
        """Turns on the test scanner."""
        self._on_scan_callback = on_scan
        self._is_running = True
        logger.info("Mock barcode scanner started.")

    def stop(self) -> None:
        """Turns off the test scanner."""
        self._is_running = False
        logger.info("Mock barcode scanner stopped.")


_scanner_instance: Optional[IBarcodeScanner] = None


def get_barcode_scanner(use_mock: bool = False) -> IBarcodeScanner:
    """
    Returns the active barcode scanner for the app.
    Uses the real Raspberry Pi camera if available, or automatically falls back
    to the test scanner if running on a computer without a camera.
    """
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
