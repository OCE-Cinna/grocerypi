"""
API routes for Raspberry Pi system actions.

This file lets the user close the full-screen Chromium kiosk browser from the
top navigation bar to return to the normal Raspberry Pi desktop, or pull the
latest code updates from GitHub when restarting the application.
"""

import logging
import os
import subprocess
from fastapi import APIRouter

logger = logging.getLogger("grocerypi.routers.system")

router = APIRouter(prefix="/system", tags=["System"])

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@router.post("/git-pull")
def git_pull_latest():
    """
    Pulls the latest commits from GitHub for the active branch so the Raspberry Pi
    kiosk updates automatically when the user taps 'Refresh / Restart Application'.
    """
    logger.info("Pulling latest GitHub updates via System Menu...")
    try:
        res = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = (res.stdout or res.stderr or "").strip()
        return {
            "status": "ok" if res.returncode == 0 else "warning",
            "output": output,
        }
    except Exception as e:
        logger.warning(f"Git pull notice: {e}")
        return {"status": "warning", "output": str(e)}


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
