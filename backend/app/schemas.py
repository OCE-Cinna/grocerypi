from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.models import ItemCategory, PreferredStore, InventoryStatus, ScanStatus


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ─── Legacy Items & Lists ─────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    quantity: Optional[str] = "1"
    unit: Optional[str] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    quantity: Optional[str] = None
    unit: Optional[str] = None
    checked: Optional[bool] = None


class ItemOut(BaseModel):
    id: int
    name: str
    quantity: str
    unit: Optional[str]
    checked: bool
    list_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class ListOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    checked_count: int = 0

    model_config = {"from_attributes": True}


class ListWithItems(ListOut):
    items: List[ItemOut] = []


# ─── Nutrition Schemas (Strict Order) ─────────────────────────────────────────

class NutritionProfile(BaseModel):
    """Nutritional metadata per 100g / serving in strict EU declaration order."""
    energy_kj: float = Field(default=0.0, ge=0.0, description="Energy in kilojoules (kJ)")
    energy_kcal: float = Field(default=0.0, ge=0.0, description="Energy in kilocalories (kcal)")
    fat_grams: float = Field(default=0.0, ge=0.0, description="Total fat in grams")
    saturated_fat_grams: float = Field(default=0.0, ge=0.0, description="Saturated fat in grams")
    carbohydrate_grams: float = Field(default=0.0, ge=0.0, description="Total carbohydrate in grams")
    sugar_grams: float = Field(default=0.0, ge=0.0, description="Sugars in grams")
    fiber_grams: float = Field(default=0.0, ge=0.0, description="Dietary fibers in grams")
    protein_grams: float = Field(default=0.0, ge=0.0, description="Protein in grams")
    salt_grams: float = Field(default=0.0, ge=0.0, description="Salt content in grams")


# ─── Product Catalog Schemas ──────────────────────────────────────────────────

class ProductCatalogBase(BaseModel):
    barcode: str = Field(..., min_length=3, max_length=32, description="EAN-13, UPC, or code-128 barcode")
    name: str = Field(..., min_length=1, max_length=150)
    brand: Optional[str] = Field(None, max_length=100)
    category: ItemCategory = ItemCategory.FOOD
    preferred_store: PreferredStore = PreferredStore.AH
    is_dual_store: bool = False
    webshop_id: Optional[int] = None
    package_size: Optional[str] = Field(None, max_length=50)

    # 9 nutritional fields in order
    energy_kj: float = Field(default=0.0, ge=0.0)
    energy_kcal: float = Field(default=0.0, ge=0.0)
    fat_grams: float = Field(default=0.0, ge=0.0)
    saturated_fat_grams: float = Field(default=0.0, ge=0.0)
    carbohydrate_grams: float = Field(default=0.0, ge=0.0)
    sugar_grams: float = Field(default=0.0, ge=0.0)
    fiber_grams: float = Field(default=0.0, ge=0.0)
    protein_grams: float = Field(default=0.0, ge=0.0)
    salt_grams: float = Field(default=0.0, ge=0.0)


class ProductCatalogCreate(ProductCatalogBase):
    pass


class ProductCatalogUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    brand: Optional[str] = None
    category: Optional[ItemCategory] = None
    preferred_store: Optional[PreferredStore] = None
    package_size: Optional[str] = None
    energy_kj: Optional[float] = Field(None, ge=0.0)
    energy_kcal: Optional[float] = Field(None, ge=0.0)
    fat_grams: Optional[float] = Field(None, ge=0.0)
    saturated_fat_grams: Optional[float] = Field(None, ge=0.0)
    carbohydrate_grams: Optional[float] = Field(None, ge=0.0)
    sugar_grams: Optional[float] = Field(None, ge=0.0)
    fiber_grams: Optional[float] = Field(None, ge=0.0)
    protein_grams: Optional[float] = Field(None, ge=0.0)
    salt_grams: Optional[float] = Field(None, ge=0.0)


class ProductCatalogOut(ProductCatalogBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Inventory Schemas ────────────────────────────────────────────────────────

class InventoryItemBase(BaseModel):
    quantity: int = Field(default=1, ge=0, description="Available stock units")
    status: InventoryStatus = InventoryStatus.IN_STOCK


class InventoryItemCreate(InventoryItemBase):
    product_id: int


class InventoryItemUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=0)
    status: Optional[InventoryStatus] = None
    manual_interval_override: Optional[float] = Field(None, ge=0.5)
    is_dual_store: Optional[bool] = None


class InventoryItemOut(InventoryItemBase):
    id: int
    product_id: int
    last_restocked_at: datetime
    predicted_depletion_at: Optional[datetime] = None
    restock_interval_days: float
    manual_interval_override: Optional[float] = None
    is_dual_store: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    product: ProductCatalogOut

    model_config = {"from_attributes": True}


# ─── Barcode Scan & Ingestion Schemas ─────────────────────────────────────────

class BarcodeScanRequest(BaseModel):
    barcode: str = Field(..., min_length=3, max_length=64, description="Scanned barcode string")
    device_info: Optional[str] = Field(default="Raspberry Pi Camera v3", max_length=100)


class BarcodeScanResponse(BaseModel):
    scan_status: ScanStatus
    message: str
    scanned_at: datetime
    barcode: str
    product: Optional[ProductCatalogOut] = None
    inventory_item: Optional[InventoryItemOut] = None


class ScanLogOut(BaseModel):
    id: int
    raw_barcode: str
    product_id: Optional[int] = None
    status: ScanStatus
    device_info: str
    scanned_at: datetime

    model_config = {"from_attributes": True}


# ─── Nutritional Aggregation Schema ───────────────────────────────────────────

class NutritionalSummaryOut(BaseModel):
    total_items_counted: int
    total_energy_kj: float
    total_energy_kcal: float
    total_fat_grams: float
    total_saturated_fat_grams: float
    total_carbohydrate_grams: float
    total_sugar_grams: float
    total_fiber_grams: float
    total_protein_grams: float
    total_salt_grams: float


# ─── Cart & Smart Replenishment Schemas ────────────────────────────────────────

class CartSuggestionItem(BaseModel):
    id: int
    store: str
    name: str
    subtext: str
    quantity_text: str
    is_dual_store: bool = False
    effective_interval_days: float
    days_since_restock: float
    current_quantity: int
    urgency: str  # "high", "medium", "normal"


class StoreQueue(BaseModel):
    id: str
    title: str
    subtitle: str
    items: list[CartSuggestionItem]


class CartSuggestionsResponse(BaseModel):
    queues: list[StoreQueue]


class PurchaseOrderItemOut(BaseModel):
    id: int
    description: str
    quantity: int
    unit_price: float
    total_price: float

    model_config = {"from_attributes": True}


class PurchaseOrderOut(BaseModel):
    id: int
    order_number: str
    order_date: datetime
    source: str
    total_amount: float
    items: list[PurchaseOrderItemOut]

    model_config = {"from_attributes": True}

