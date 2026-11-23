"""
GroceryPi Database Seeder (from Local AH Product Cache & Household Staples).

Populates the local SQLite database (grocerypi.db) using the real Albert Heijn
product cache (backend/app/db/ah_product_cache.json) along with core Dutch
household staples across AH, Jumbo, and Lidl. Includes real EAN-13 barcodes,
Nutri-Scores (A to E), vegan/vegetarian flags, package sizes, and all 9
European nutrition values per 100g.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from typing import Any, Dict, List

from app.database import Base, SessionLocal, engine, init_db
from app.models import InventoryItem, InventoryStatus, ItemCategory, PreferredStore, ProductCatalog
from app.services.ah_client import clean_product_name_and_brand, map_category

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grocerypi.seed")

CACHE_PATH = os.path.join(os.path.dirname(__file__), "ah_product_cache.json")

DUAL_STORE_KEYWORDS = [
    "zeep", "afwas", "toiletpapier", "keukenrol", "schoonmaak", "dreft",
    "melk", "eieren", "bananen", "brood", "boter", "kaas", "ui", "knoflook",
]

# Core household items ensuring all 4 categories (Food, Pets, Household, Hygiene)
# and all 3 stores (AH, Jumbo, Lidl) are represented in the active inventory
CORE_SEED_PRODUCTS: List[Dict[str, Any]] = [
    {
        "barcode": "8710400035541",
        "name": "Pindakaas Original",
        "brand": "Calvé",
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "350g",
        "nutriscore": "A",
        "is_vegetarian": True,
        "is_vegan": True,
        "energy_kj": 2773.0,
        "energy_kcal": 664.0,
        "fat_grams": 58.0,
        "saturated_fat_grams": 8.5,
        "carbohydrate_grams": 11.0,
        "sugar_grams": 6.4,
        "fiber_grams": 6.6,
        "protein_grams": 21.0,
        "salt_grams": 0.55,
        "initial_qty": 2,
        "interval_days": 14.0,
        "days_ago": 5,
    },
    {
        "barcode": "8718906001007",
        "name": "Zaanse Halfvolle Melk",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "1 L",
        "nutriscore": "B",
        "is_vegetarian": True,
        "is_vegan": False,
        "energy_kj": 198.0,
        "energy_kcal": 47.0,
        "fat_grams": 1.5,
        "saturated_fat_grams": 1.1,
        "carbohydrate_grams": 4.8,
        "sugar_grams": 4.8,
        "fiber_grams": 0.0,
        "protein_grams": 3.6,
        "salt_grams": 0.11,
        "initial_qty": 2,
        "interval_days": 7.0,
        "days_ago": 6,
    },
    {
        "barcode": "8718907058864",
        "name": "Volkoren Havervlokken",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.LIDL,
        "package_size": "500g",
        "nutriscore": "A",
        "is_vegetarian": True,
        "is_vegan": True,
        "energy_kj": 1530.0,
        "energy_kcal": 363.0,
        "fat_grams": 6.9,
        "saturated_fat_grams": 1.2,
        "carbohydrate_grams": 56.0,
        "sugar_grams": 1.3,
        "fiber_grams": 10.0,
        "protein_grams": 14.0,
        "salt_grams": 0.03,
        "initial_qty": 1,
        "interval_days": 14.0,
        "days_ago": 11,
    },
    {
        "barcode": "8710400010050",
        "name": "Hagelslag Melk",
        "brand": "De Ruijter",
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.JUMBO,
        "package_size": "380g",
        "nutriscore": "E",
        "is_vegetarian": True,
        "is_vegan": False,
        "energy_kj": 1850.0,
        "energy_kcal": 439.0,
        "fat_grams": 15.0,
        "saturated_fat_grams": 9.1,
        "carbohydrate_grams": 70.0,
        "sugar_grams": 68.0,
        "fiber_grams": 4.2,
        "protein_grams": 5.4,
        "salt_grams": 0.12,
        "initial_qty": 1,
        "interval_days": 21.0,
        "days_ago": 8,
    },
    {
        "barcode": "8718452134567",
        "name": "Volkoren Penne Rigate",
        "brand": "Jumbo",
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.JUMBO,
        "package_size": "500g",
        "nutriscore": "A",
        "is_vegetarian": True,
        "is_vegan": True,
        "energy_kj": 1475.0,
        "energy_kcal": 349.0,
        "fat_grams": 2.5,
        "saturated_fat_grams": 0.5,
        "carbohydrate_grams": 65.0,
        "sugar_grams": 3.0,
        "fiber_grams": 8.0,
        "protein_grams": 12.5,
        "salt_grams": 0.01,
        "initial_qty": 3,
        "interval_days": 14.0,
        "days_ago": 4,
    },
    {
        "barcode": "8718907102932",
        "name": "Scharreleieren Klasse M",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "10 stuks",
        "nutriscore": "A",
        "is_vegetarian": True,
        "is_vegan": False,
        "energy_kj": 548.0,
        "energy_kcal": 131.0,
        "fat_grams": 9.3,
        "saturated_fat_grams": 2.7,
        "carbohydrate_grams": 0.2,
        "sugar_grams": 0.2,
        "fiber_grams": 0.0,
        "protein_grams": 12.3,
        "salt_grams": 0.38,
        "initial_qty": 1,
        "interval_days": 10.0,
        "days_ago": 9,
    },
    {
        "barcode": "8710400140023",
        "name": "Wasmiddel Vloeibaar Stralend Wit",
        "brand": "Robijn",
        "category": ItemCategory.HOUSEHOLD,
        "preferred_store": PreferredStore.JUMBO,
        "is_dual_store": True,
        "package_size": "1 L",
        "nutriscore": None,
        "is_vegetarian": False,
        "is_vegan": False,
        "initial_qty": 1,
        "interval_days": 30.0,
        "days_ago": 24,
    },
    {
        "barcode": "8718906103985",
        "name": "Vaatwastabletten All-in-1",
        "brand": None,
        "category": ItemCategory.HOUSEHOLD,
        "preferred_store": PreferredStore.AH,
        "is_dual_store": True,
        "package_size": "40 stuks",
        "nutriscore": None,
        "is_vegetarian": False,
        "is_vegan": False,
        "initial_qty": 1,
        "interval_days": 28.0,
        "days_ago": 15,
    },
    {
        "barcode": "8718906501231",
        "name": "Tandpasta Fresh & Clean",
        "brand": None,
        "category": ItemCategory.HYGIENE,
        "preferred_store": PreferredStore.AH,
        "package_size": "75ml",
        "nutriscore": None,
        "is_vegetarian": False,
        "is_vegan": True,
        "initial_qty": 2,
        "interval_days": 28.0,
        "days_ago": 10,
    },
    {
        "barcode": "8718906204569",
        "name": "Kattenbrokjes Zalm & Groente",
        "brand": None,
        "category": ItemCategory.PET,
        "preferred_store": PreferredStore.AH,
        "package_size": "1.5kg",
        "nutriscore": None,
        "is_vegetarian": False,
        "is_vegan": False,
        "energy_kj": 1600.0,
        "energy_kcal": 382.0,
        "fat_grams": 14.0,
        "saturated_fat_grams": 4.5,
        "carbohydrate_grams": 35.0,
        "sugar_grams": 2.0,
        "fiber_grams": 3.0,
        "protein_grams": 32.0,
        "salt_grams": 1.2,
        "initial_qty": 1,
        "interval_days": 21.0,
        "days_ago": 16,
    },
]


def _generate_fallback_barcode(name: str) -> str:
    """Generates a consistent 13-digit internal barcode for cached items without a GTIN."""
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()
    numeric_chunk = str(int(h[:12], 16))[:9].zfill(9)
    prefix = f"200{numeric_chunk}"
    total = sum((int(d) * (3 if i % 2 == 1 else 1)) for i, d in enumerate(prefix))
    check_digit = (10 - (total % 10)) % 10
    return f"{prefix}{check_digit}"


def _extract_nutrition_from_detail(detail: Dict[str, Any]) -> Dict[str, float]:
    """Extracts the 9 European nutrition metrics from a cached AH detail entry."""
    nutrition_facts: Dict[str, float] = {
        "energy_kj": 0.0,
        "energy_kcal": 0.0,
        "fat_grams": 0.0,
        "saturated_fat_grams": 0.0,
        "carbohydrate_grams": 0.0,
        "sugar_grams": 0.0,
        "fiber_grams": 0.0,
        "protein_grams": 0.0,
        "salt_grams": 0.0,
    }
    if not detail:
        return nutrition_facts

    trade_item = detail.get("tradeItem") or {}
    nutri_info = trade_item.get("nutritionalInformation") or {}
    headers_list = nutri_info.get("nutrientHeaders") or []
    if headers_list:
        details = headers_list[0].get("nutrientDetail") or []
        for d in details:
            code = (d.get("nutrientTypeCode") or {}).get("value")
            qty_contained = d.get("quantityContained") or []
            if qty_contained and code:
                val = qty_contained[0].get("value")
                unit = (qty_contained[0].get("measurementUnitCode") or {}).get("value")
                if val is not None:
                    try:
                        fval = float(val)
                        if code == "ENER-" and unit == "kJ":
                            nutrition_facts["energy_kj"] = fval
                        elif code == "ENER-" and unit == "kcal":
                            nutrition_facts["energy_kcal"] = fval
                        elif code == "FAT":
                            nutrition_facts["fat_grams"] = fval
                        elif code == "FASAT":
                            nutrition_facts["saturated_fat_grams"] = fval
                        elif code == "CHOAVL":
                            nutrition_facts["carbohydrate_grams"] = fval
                        elif code == "SUGAR-":
                            nutrition_facts["sugar_grams"] = fval
                        elif code == "FIBTG":
                            nutrition_facts["fiber_grams"] = fval
                        elif code == "PRO-":
                            nutrition_facts["protein_grams"] = fval
                        elif code == "SALTEQ":
                            nutrition_facts["salt_grams"] = fval
                    except ValueError:
                        pass
    return nutrition_facts


def seed_database(reset: bool = False) -> None:
    """
    Populates the SQLite database with products from ah_product_cache.json and
    CORE_SEED_PRODUCTS, seeding realistic kitchen stock for the kiosk UI.
    """
    if reset:
        logger.info("Resetting tables for fresh database seed...")
        Base.metadata.drop_all(bind=engine)

    init_db()
    db = SessionLocal()
    now_utc = datetime.now(timezone.utc)

    try:
        inserted_catalog = 0
        inserted_inventory = 0

        # 1. Seed Core Products first
        for item_cfg in CORE_SEED_PRODUCTS:
            data = dict(item_cfg)
            initial_qty = data.pop("initial_qty", 1)
            interval_days = data.pop("interval_days", 7.0)
            days_ago = data.pop("days_ago", 2)
            barcode = data["barcode"]

            prod = db.query(ProductCatalog).filter(ProductCatalog.barcode == barcode).first()
            if not prod:
                prod = ProductCatalog(**data)
                db.add(prod)
                db.flush()
                inserted_catalog += 1

            inv = db.query(InventoryItem).filter(InventoryItem.product_id == prod.id).first()
            if not inv:
                inv = InventoryItem(
                    product_id=prod.id,
                    quantity=initial_qty,
                    status=InventoryStatus.IN_STOCK,
                    last_restocked_at=now_utc - timedelta(days=days_ago),
                    restock_interval_days=interval_days,
                    is_dual_store=bool(prod.is_dual_store),
                )
                db.add(inv)
                inserted_inventory += 1

        # 2. Load real household products from ah_product_cache.json
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            search_keys = [k for k in cache_data.keys() if k.startswith("search:")]
            for idx, sk in enumerate(search_keys):
                search_res = cache_data[sk]
                if not isinstance(search_res, dict):
                    continue

                webshop_id = search_res.get("webshopId")
                detail = cache_data.get(f"detail:{webshop_id}") if webshop_id else None

                gtin = None
                if isinstance(detail, dict):
                    gtin = (detail.get("tradeItem") or {}).get("gtin")
                    if gtin and len(gtin) == 14 and gtin.startswith("0"):
                        gtin = gtin[1:]

                raw_title = search_res.get("title") or sk.replace("search:", "")
                raw_brand = search_res.get("brand")
                clean_name, clean_brand = clean_product_name_and_brand(raw_title, raw_brand)

                barcode = gtin or _generate_fallback_barcode(clean_name)
                if db.query(ProductCatalog).filter(ProductCatalog.barcode == barcode).first():
                    continue

                prop_icons = [str(p).lower() for p in (search_res.get("propertyIcons") or [])]
                is_vegan = "vegan" in prop_icons
                is_veg = is_vegan or "vega" in prop_icons or "vegetarisch" in prop_icons

                nutriscore_val = search_res.get("nutriscore")
                nutriscore_str = (
                    str(nutriscore_val).upper()
                    if nutriscore_val in ["A", "B", "C", "D", "E"]
                    else None
                )

                main_cat = str(search_res.get("mainCategory") or "")
                sub_cat = str(search_res.get("subCategory") or "")
                category = map_category(main_cat, sub_cat, clean_name)
                is_dual = any(k in clean_name.lower() for k in DUAL_STORE_KEYWORDS)
                nutrition = _extract_nutrition_from_detail(detail if isinstance(detail, dict) else {})

                prod = ProductCatalog(
                    barcode=barcode,
                    name=clean_name,
                    brand=clean_brand,
                    category=category,
                    preferred_store=PreferredStore.AH,
                    is_dual_store=is_dual,
                    webshop_id=webshop_id,
                    package_size=search_res.get("salesUnitSize"),
                    nutriscore=nutriscore_str,
                    is_vegetarian=is_veg,
                    is_vegan=is_vegan,
                    **nutrition,
                )
                db.add(prod)
                db.flush()
                inserted_catalog += 1

                # Seed the first 40 cached household items into active kitchen inventory
                if idx < 40:
                    days_ago = (idx % 12) + 1
                    interval_days = 7.0 if category == ItemCategory.FOOD else 21.0
                    inv = InventoryItem(
                        product_id=prod.id,
                        quantity=2 if idx % 3 == 0 else 1,
                        status=InventoryStatus.IN_STOCK,
                        last_restocked_at=now_utc - timedelta(days=days_ago),
                        restock_interval_days=interval_days,
                        is_dual_store=is_dual,
                    )
                    db.add(inv)
                    inserted_inventory += 1

        db.commit()
        logger.info(
            f"Database seeded: +{inserted_catalog} catalog items, +{inserted_inventory} active inventory items."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(reset=True)
