"""
Database connection setup for GroceryPi.

This file connects the backend to the local SQLite database file (grocerypi.db).
It also configures the database so the camera scanner and the touch screen can
read and save data at the same time without slowing each other down.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "grocerypi.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Allow multiple background tasks (like the camera and web requests) to share SQLite safely
connect_args = {"check_same_thread": False, "timeout": 30.0} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """
        Turns on fast database settings (WAL mode and memory cache) every time
        the app connects to SQLite, preventing the screen from freezing during scans.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA temp_store = MEMORY;")
        cursor.execute("PRAGMA cache_size = -64000;")  # Use 64MB RAM cache
        cursor.execute("PRAGMA mmap_size = 268435456;")  # Fast file reading
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class used by all database tables in models.py."""
    pass


def init_db():
    """
    Creates all database tables and adds any new columns if an older database
    file is being used.
    """
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Check if older tables need new columns added
    with engine.connect() as conn:
        from sqlalchemy import text
        res = conn.execute(text("PRAGMA table_info(product_catalog);")).fetchall()
        prod_cols = [r[1] for r in res]
        if "is_dual_store" not in prod_cols:
            conn.execute(text("ALTER TABLE product_catalog ADD COLUMN is_dual_store BOOLEAN DEFAULT 0 NOT NULL;"))
        if "webshop_id" not in prod_cols:
            conn.execute(text("ALTER TABLE product_catalog ADD COLUMN webshop_id INTEGER;"))
        if "nutriscore" not in prod_cols:
            conn.execute(text("ALTER TABLE product_catalog ADD COLUMN nutriscore VARCHAR(5);"))
        if "is_vegetarian" not in prod_cols:
            conn.execute(text("ALTER TABLE product_catalog ADD COLUMN is_vegetarian BOOLEAN DEFAULT 0 NOT NULL;"))
        if "is_vegan" not in prod_cols:
            conn.execute(text("ALTER TABLE product_catalog ADD COLUMN is_vegan BOOLEAN DEFAULT 0 NOT NULL;"))
        if "is_frozen" not in prod_cols:
            conn.execute(text("ALTER TABLE product_catalog ADD COLUMN is_frozen BOOLEAN DEFAULT 0 NOT NULL;"))

        res = conn.execute(text("PRAGMA table_info(inventory_items);")).fetchall()
        inv_cols = [r[1] for r in res]
        if "is_dual_store" not in inv_cols:
            conn.execute(text("ALTER TABLE inventory_items ADD COLUMN is_dual_store BOOLEAN DEFAULT 0 NOT NULL;"))
        if "manual_interval_override" not in inv_cols:
            conn.execute(text("ALTER TABLE inventory_items ADD COLUMN manual_interval_override FLOAT;"))
        conn.commit()


def get_db():
    """
    Opens a temporary connection to the database for an API request and closes
    it automatically when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
