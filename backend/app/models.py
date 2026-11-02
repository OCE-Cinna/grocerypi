from datetime import datetime, timezone
import enum
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────────

class ItemCategory(str, enum.Enum):
    FOOD = "Food"
    HOUSEHOLD = "Household"
    HYGIENE = "Hygiene"
    PET = "Pet"


class PreferredStore(str, enum.Enum):
    AH = "AH"
    JUMBO = "Jumbo"
    LIDL = "Lidl"
    OTHER = "Other"


class InventoryStatus(str, enum.Enum):
    IN_STOCK = "IN_STOCK"
    DEPLETED = "DEPLETED"
    PREDICTED_LOW = "PREDICTED_LOW"


class ScanStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    UNKNOWN_BARCODE = "UNKNOWN_BARCODE"
    ERROR = "ERROR"


# ─── Auth & Legacy Lists ─────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    lists = relationship("GroceryList", back_populates="owner", cascade="all, delete-orphan")


class GroceryList(Base):
    __tablename__ = "grocery_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship("User", back_populates="lists")
    items = relationship("Item", back_populates="grocery_list", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    quantity = Column(String(50), default="1")
    unit = Column(String(30), nullable=True)
    checked = Column(Boolean, default=False)
    list_id = Column(Integer, ForeignKey("grocery_lists.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    grocery_list = relationship("GroceryList", back_populates="items")


# ─── GroceryPi Inventory & Barcode Domain Models ─────────────────────────────

class ProductCatalog(Base):
    """Global or household product reference mapped by unique barcode (e.g. EAN-13)."""
    __tablename__ = "product_catalog"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    brand = Column(String(100), nullable=True)
    category = Column(SAEnum(ItemCategory), default=ItemCategory.FOOD, nullable=False)
    preferred_store = Column(SAEnum(PreferredStore), default=PreferredStore.AH, nullable=False)
    is_dual_store = Column(Boolean, default=False, nullable=False)
    webshop_id = Column(Integer, nullable=True, index=True)
    package_size = Column(String(50), nullable=True)

    # Nutritional metadata per 100g / serving (Strict Order: Energy kJ/kcal, Fat, SatFat, Carbs, Sugar, Fiber, Protein, Salt)
    energy_kj = Column(Float, default=0.0, nullable=False)
    energy_kcal = Column(Float, default=0.0, nullable=False)
    fat_grams = Column(Float, default=0.0, nullable=False)
    saturated_fat_grams = Column(Float, default=0.0, nullable=False)
    carbohydrate_grams = Column(Float, default=0.0, nullable=False)
    sugar_grams = Column(Float, default=0.0, nullable=False)
    fiber_grams = Column(Float, default=0.0, nullable=False)
    protein_grams = Column(Float, default=0.0, nullable=False)
    salt_grams = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    inventory_items = relationship("InventoryItem", back_populates="product", cascade="all, delete-orphan")
    scan_logs = relationship("ScanLog", back_populates="product")


class InventoryItem(Base):
    """Tracks current physical stock and consumption intervals under the 'Items IN' paradigm."""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product_catalog.id"), unique=True, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    status = Column(SAEnum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)
    
    last_restocked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    predicted_depletion_at = Column(DateTime(timezone=True), nullable=True)
    restock_interval_days = Column(Float, default=7.0, nullable=False)  # rolling average days between restocks
    manual_interval_override = Column(Float, nullable=True)  # user-configured override for dual-store/Jumbo purchases
    is_dual_store = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    product = relationship("ProductCatalog", back_populates="inventory_items")


class ScanLog(Base):
    """Audit log of raw optical barcode reads dispatched from the hardware sensor."""
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    raw_barcode = Column(String(64), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("product_catalog.id"), nullable=True)
    status = Column(SAEnum(ScanStatus), default=ScanStatus.SUCCESS, nullable=False)
    device_info = Column(String(100), default="Raspberry Pi Camera v3", nullable=False)
    scanned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    product = relationship("ProductCatalog", back_populates="scan_logs")


# ─── Receipt & Purchase Order History ────────────────────────────────────────

class PurchaseOrder(Base):
    """Historical supermarket invoices (AH, Jumbo, etc.) for empirical replenishment modeling."""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(64), unique=True, index=True, nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(32), default="AH", nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    """Individual line items parsed from historical invoices."""
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("product_catalog.id"), nullable=True)
    description = Column(String(200), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    total_price = Column(Float, default=0.0, nullable=False)

    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("ProductCatalog")

