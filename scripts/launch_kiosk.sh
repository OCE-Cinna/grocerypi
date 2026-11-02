#!/usr/bin/env bash
# ==============================================================================
# GroceryPi Local Kiosk Launcher
# Starts FastAPI backend, Frontend dev server, and launches Chromium in Kiosk Mode.
# ==============================================================================

set -e

# Resolve base repository directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Ensure environment paths
export PATH="/home/grocerypi/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export ENABLE_HARDWARE_SCANNER=true
export CAMERA_VFLIP=true

echo "=========================================="
echo " Starting GroceryPi Kiosk Environment..."
echo " Root: $SCRIPT_DIR"
echo "=========================================="

# 1. Start FastAPI Backend if not running on port 8000
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "[Backend] Already running on port 8000."
else
    echo "[Backend] Starting FastAPI backend service..."
    cd "$SCRIPT_DIR/backend"
    PYTHONPATH=. ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/grocerypi_backend.log 2>&1 &
    BACKEND_PID=$!
    echo "[Backend] Started with PID $BACKEND_PID."
    cd "$SCRIPT_DIR"
fi

# 2. Start Frontend server if not running on port 5173
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "[Frontend] Already running on port 5173."
else
    echo "[Frontend] Starting Frontend server on port 5173..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/grocerypi_frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "[Frontend] Started with PID $FRONTEND_PID."
    cd "$SCRIPT_DIR"
fi

# 3. Wait for backend and frontend services to be responsive
echo "[Launcher] Waiting for services to become ready..."
for i in $(seq 1 30); do
    BACKEND_OK=0
    FRONTEND_OK=0
    
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        BACKEND_OK=1
    fi
    if curl -s http://localhost:5173/ > /dev/null 2>&1; then
        FRONTEND_OK=1
    fi

    if [ "$BACKEND_OK" -eq 1 ] && [ "$FRONTEND_OK" -eq 1 ]; then
        echo "[Launcher] Both Backend and Frontend are ready!"
        break
    fi
    sleep 0.5
done

# 4. Resolve Chromium browser binary
CHROMIUM_BIN=$(which chromium-browser 2>/dev/null || which chromium 2>/dev/null || echo "")

if [ -z "$CHROMIUM_BIN" ]; then
    echo "[Error] Chromium not found in PATH." >&2
    exit 1
fi

echo "[Chromium] Launching $CHROMIUM_BIN in fullscreen Kiosk Mode..."

# 5. Launch Chromium in Kiosk Mode
# Note: Tapping 'Home' inside GroceryPi triggers POST /system/exit-kiosk,
# which cleanly closes this Chromium window and returns to the Raspberry Pi desktop.
exec "$CHROMIUM_BIN" \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-features=Translate \
    --disable-session-crashed-bubble \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --check-for-update-interval=31536000 \
    --password-store=basic \
    --autoplay-policy=no-user-gesture-required \
    http://localhost:5173

