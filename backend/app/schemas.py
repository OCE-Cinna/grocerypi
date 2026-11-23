"""
Data formats (schemas) for GroceryPi API requests and responses.

This file checks that data coming into the backend (like a scanned barcode or
a quantity change) is valid, and formats data sent back to the React screen.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from app.models import InventoryStatus, ItemCategory, PreferredStore, ScanStatus


# ─── User Login & Registration Formats ────────────────────────────────────────

class UserRegister(BaseModel):
    """Data required when creating a new user account."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Data required when logging in with a username and password."""
    username: str
    password: str


class UserOut(BaseModel):
    """Safe user account details returned to the frontend (without the password)."""
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Login token sent back after a user signs in successfully."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ─── Custom List Formats ──────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    """Data required to add a manual item to a custom list."""
    name: str = Field(..., min_length=1, max_length=150)
    quantity: Optional[str] = "1"
    unit: Optional[str] = None


class ItemUpdate(BaseModel):
    """Fields that can be changed on a custom list item."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    quantity: Optional[str] = None
    unit: Optional[str] = None
    checked: Optional[bool] = None


class ItemOut(BaseModel):
    """Format used when sending a custom list item to the frontend."""
    id: int
    name: str
    quantity: str
    unit: Optional[str]
    checked: bool
    list_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ListCreate(BaseModel):
    """Data required to create a new custom grocery list."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ListUpdate(BaseModel):
    """Fields that can be updated on a custom grocery list."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class ListOut(BaseModel):
    """Summary information for a custom grocery list."""
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
    """A custom grocery list including all of its items."""
    items: List[ItemOut] = []


# ─── Nutrition Format ─────────────────────────────────────────────────────────

class NutritionProfile(BaseModel):
    """Stores the 9 standard European nutrition values per 100g of a product."""
    energy_kj: float = Field(default=0.0, ge=0.0, description="Energy in kilojoules (kJ)")
    energy_kcal: float = Field(default=0.0, ge=0.0, description="Energy in kilocalories (kcal)")
    fat_grams: float = Field(default=0.0, ge=0.0, description="Total fat in grams")
    saturated_fat_grams: float = Field(default=0.0, ge=0.0, description="Saturated fat in grams")
    carbohydrate_grams: float = Field(default=0.0, ge=0.0, description="Total carbohydrates in grams")
    sugar_grams: float = Field(default=0.0, ge=0.0, description="Sugars in grams")
    fiber_grams: float = Field(default=0.0, ge=0.0, description="Dietary fiber in grams")
    protein_grams: float = Field(default=0.0, ge=0.0, description="Protein in grams")
    salt_grams: float = Field(default=0.0, ge=0.0, description="Salt in grams")


# ─── Product Catalog Formats ──────────────────────────────────────────────────

class ProductCatalogBase(BaseModel):
    """Shared fields for any product in the catalog, including barcode, store, and nutrition."""
    barcode: str = Field(..., min_length=3, max_length=32, description="Product barcode number")
    name: str = Field(..., min_length=1, max_length=150)
    brand: Optional[str] = Field(None, max_length=100)
    category: ItemCategory = ItemCategory.FOOD
    preferred_store: PreferredStore = PreferredStore.AH
    is_dual_store: bool = False
    webshop_id: Optional[int] = None
    package_size: Optional[str] = Field(None, max_length=50)
    nutriscore: Optional[str] = Field(None, max_length=5)
    is_vegetarian: bool = False
    is_vegan: bool = False

    # 9 nutrition values in standard European order
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
    """Data required when adding a new product to the catalog."""
    pass


class ProductCatalogUpdate(BaseModel):
    """Fields that can be edited on an existing catalog product."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    brand: Optional[str] = None
    category: Optional[ItemCategory] = None
    preferred_store: Optional[PreferredStore] = None
    package_size: Optional[str] = None
    nutriscore: Optional[str] = None
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
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
    """Product details returned to the frontend screen."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Kitchen Inventory Formats ────────────────────────────────────────────────

class InventoryItemBase(BaseModel):
    """Basic stock count and status for an inventory item."""
    quantity: int = Field(default=1, ge=0, description="Number of units currently in stock")
    status: InventoryStatus = InventoryStatus.IN_STOCK


class InventoryItemCreate(InventoryItemBase):
    """Data needed to create a new inventory entry for a product."""
    product_id: int


class InventoryItemUpdate(BaseModel):
    """Fields that can be updated when the user taps +/- or edits an inventory item."""
    quantity: Optional[int] = Field(None, ge=0)
    status: Optional[InventoryStatus] = None
    manual_interval_override: Optional[float] = Field(None, ge=0.5)
    is_dual_store: Optional[bool] = None


class InventoryItemOut(InventoryItemBase):
    """Complete inventory item details sent to the Dashboard screen, including product info."""
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


# ─── Barcode Scan Formats ─────────────────────────────────────────────────────

class BarcodeScanRequest(BaseModel):
    """Data sent to the backend when a barcode is scanned or typed in."""
    barcode: str = Field(..., min_length=3, max_length=64, description="Scanned barcode text")
    device_info: Optional[str] = Field(default="Raspberry Pi Camera v3", max_length=100)
    confirm_unknown: bool = Field(
        default=False,
        description="When True, confirms adding an unrecognized barcode as a custom placeholder item.",
    )


class BarcodeScanResponse(BaseModel):
    """Confirmation message and updated stock details returned after a barcode scan."""
    scan_status: ScanStatus
    message: str
    scanned_at: datetime
    barcode: str
    product: Optional[ProductCatalogOut] = None
    inventory_item: Optional[InventoryItemOut] = None


class ScanLogOut(BaseModel):
    """A single entry in the recent barcode scan history log."""
    id: int
    raw_barcode: str
    product_id: Optional[int] = None
    status: ScanStatus
    device_info: str
    scanned_at: datetime

    model_config = {"from_attributes": True}


# ─── Nutrition Summary Format ─────────────────────────────────────────────────

class NutritionalSummaryOut(BaseModel):
    """Total nutrition values, average Nutri-Score, and diet counts for all stocked food."""
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
    average_nutriscore: Optional[str] = None
    average_nutriscore_numeric: Optional[float] = None
    total_vegetarian_items: int = 0
    total_vegan_items: int = 0
    nutriscore_counts: Optional[dict[str, int]] = None


# ─── Shopping Cart & Restock Suggestion Formats ───────────────────────────────

class CartSuggestionItem(BaseModel):
    """A single item recommended for restocking on the Shopping Cart screen."""
    id: int
    store: str
    name: str
    brand: Optional[str] = None
    subtext: str
    quantity_text: str
    is_dual_store: bool = False
    effective_interval_days: float
    days_since_restock: float
    current_quantity: int
    urgency: str  # "high", "medium", or "normal"


class StoreQueue(BaseModel):
    """A list of recommended restock items grouped for one supermarket (AH, Jumbo, or Lidl)."""
    id: str
    title: str
    subtitle: str
    items: list[CartSuggestionItem]


class CartSuggestionsResponse(BaseModel):
    """All supermarket restock lists sent to the Shopping Cart screen."""
    queues: list[StoreQueue]


class PurchaseOrderItemOut(BaseModel):
    """A single product line from a past supermarket receipt."""
    id: int
    description: str
    quantity: int
    unit_price: float
    total_price: float

    model_config = {"from_attributes": True}


class PurchaseOrderOut(BaseModel):
    """Summary of a past supermarket receipt."""
    id: int
    order_number: str
    order_date: datetime
    source: str
    total_amount: float
    items: list[PurchaseOrderItemOut]

    model_config = {"from_attributes": True}
