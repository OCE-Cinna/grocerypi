from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, lists, items

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GroceryPi API",
    description="Smart grocery tracker API — runs on your Raspberry Pi.",
    version="1.0.0",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# In production on your Pi, restrict origins to your local network IP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(lists.router)
app.include_router(items.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "GroceryPi API"}
