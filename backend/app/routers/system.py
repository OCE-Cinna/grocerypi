"""
API routes for Raspberry Pi system actions.

This file lets the user close the full-screen Chromium kiosk browser from the
top navigation bar to return to the normal Raspberry Pi desktop when needed.
"""

import logging
import subprocess
from fastapi import APIRouter

logger = logging.getLogger("grocerypi.routers.system")

router = APIRouter(prefix="/system", tags=["System"])


@router.post("/exit-kiosk")
def exit_kiosk():
    """Closes the full-screen kiosk browser window and returns to the Pi desktop."""
    logger.info("Exit kiosk requested via Home button.")
    try:
        subprocess.Popen(
            ["sh", "-c", "pkill -f 'chromium.*--kiosk' || pkill -f 'chromium-browser.*--kiosk' || pkill -f 'chromium'"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"status": "ok", "message": "Closing kiosk mode..."}
    except Exception as e:
        logger.error(f"Error terminating kiosk: {e}")
        return {"status": "error", "message": str(e)}
