from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "grocerypi.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# SQLite needs check_same_thread=False for multi-threaded use and reasonable timeout
connect_args = {"check_same_thread": False, "timeout": 30.0} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Sets high-efficiency SQLite pragmas (WAL mode, memory cache, fast sync)."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA temp_store = MEMORY;")
        cursor.execute("PRAGMA cache_size = -64000;")  # 64MB RAM cache
        cursor.execute("PRAGMA mmap_size = 268435456;")  # 256MB memory mapped I/O
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """Initializes tables and applies lightweight SQLite migrations for added columns."""
    from app import models
    Base.metadata.create_all(bind=engine)
    
    # Safe schema alterations for SQLite
    with engine.connect() as conn:
        from sqlalchemy import text
        # Check product_catalog columns
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

        # Check inventory_items columns
        res = conn.execute(text("PRAGMA table_info(inventory_items);")).fetchall()
        inv_cols = [r[1] for r in res]
        if "is_dual_store" not in inv_cols:
            conn.execute(text("ALTER TABLE inventory_items ADD COLUMN is_dual_store BOOLEAN DEFAULT 0 NOT NULL;"))
        if "manual_interval_override" not in inv_cols:
            conn.execute(text("ALTER TABLE inventory_items ADD COLUMN manual_interval_override FLOAT;"))
        conn.commit()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
