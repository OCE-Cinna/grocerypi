"""
Albert Heijn Invoice Parser & Database Seeder for GroceryPi
Parses all historical PDF facturen in /home/grocerypi/Downloads/ah/,
extracts line items, computes empirical replenishment intervals (Delta Days / Units),
resolves GTIN barcodes & 9-metric European nutritional profiles via AH Mobile API,
and seeds the GroceryPi SQLite database.
"""

from collections import defaultdict
from datetime import datetime, timezone
import glob
import hashlib
import logging
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Set, Tuple

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import models
from app.database import SessionLocal, init_db
from app.services.ah_client import AHClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("grocerypi.ah_seeder")

MONTH_MAP = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11, "december": 12
}

# Dual-store candidates (household staples & fresh items frequently bought physically at Jumbo)
DUAL_STORE_KEYWORDS = [
    "zeep", "afwas", "toiletpapier", "keukenrol", "schoonmaak", "dreft",
    "melk", "eieren", "bananen", "brood", "boter", "kaas", "ui", "knoflook"
]

NON_GROCERY_TERMS = {
    "bezorgkosten", "plastic tasje(s)", "ah klapkrat", "klapkrat",
    "+ statiegeld", "statiegeld", "krat", "tasje"
}


def normalize_item_name(raw_name: str) -> str:
    """
    Cleans raw item descriptions:
    - Removes 'AH' or 'Albert Heijn' prefix/tag
    - Strips marketing promo tags like BONUS or voordeel
    """
    name = raw_name
    for tag in [" BONUS", " bonus", " voordeel", " VOORDEEL", " 1+1 gratis", " stapelkorting", " 2e halve prijs"]:
        name = name.replace(tag, "")
    # Strip leading or isolated AH / Albert Heijn
    name = re.sub(r"^(AH|Albert Heijn)\s+", "", name, flags=re.IGNORECASE).strip()
    name = re.sub(r"\s+\b(AH|Albert Heijn)\b", "", name, flags=re.IGNORECASE).strip()
    return re.sub(r"\s+", " ", name).strip()


def clean_brand(brand: Optional[str], product_name: str) -> Optional[str]:
    """
    If brand is AH/Albert Heijn, remove it.
    Only keep brand if it's not already in the name of the product.
    """
    if not brand:
        return None
    b = brand.strip()
    if b.lower() in ["ah", "albert heijn", "ah biologisch", "ah terra", "ah basic"]:
        return None
    if b.lower() in product_name.lower():
        return None
    return b


def infer_category(name: str) -> models.ItemCategory:
    """Infer ItemCategory from product description."""
    n = name.lower()
    if any(k in n for k in ["hond", "kat", "whiskas", "pedigree", "felix", "purina", "brokken"]):
        return models.ItemCategory.PET
    if any(k in n for k in ["toiletpapier", "shampoo", "tandpasta", "douche", "zeep", "deodorant", "watten"]):
        return models.ItemCategory.HYGIENE
    if any(k in n for k in ["afwas", "dreft", "allesreiniger", "vaatwas", "wasmiddel", "keukenrol", "vuilnis"]):
        return models.ItemCategory.HOUSEHOLD
    return models.ItemCategory.FOOD


def generate_fallback_barcode(name: str) -> str:
    """Generate a deterministic 13-digit EAN-like barcode starting with 200 (internal use prefix)."""
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()
    # 200 + 9 numeric digits + 1 check digit
    numeric_chunk = str(int(h[:12], 16))[:9].zfill(9)
    prefix = f"200{numeric_chunk}"
    # Calculate EAN-13 check digit
    total = sum((int(d) * (3 if i % 2 == 1 else 1)) for i, d in enumerate(prefix))
    check_digit = (10 - (total % 10)) % 10
    return f"{prefix}{check_digit}"


def parse_invoices_directory(ah_dir: str) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """
    Parses all PDFs in directory.
    Returns:
      orders: {order_num: {date, items, total_amount, pdf_file}}
      item_history: {normalized_name: [{date, qty, price, order_num, raw_name}]}
    """
    pdf_files = sorted(glob.glob(os.path.join(ah_dir, "*.pdf")))
    orders: Dict[str, Any] = {}
    item_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    logger.info(f"Found {len(pdf_files)} PDF files in {ah_dir}")

    for pdf_path in pdf_files:
        try:
            txt = subprocess.check_output(["pdftotext", "-layout", pdf_path, "-"]).decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Failed to read {pdf_path}: {e}")
            continue

        m_inv = re.search(r"Factuurnummer\s+([0-9\-]+)", txt)
        if not m_inv:
            continue
        order_num = m_inv.group(1)

        # Skip duplicate revision files if order already captured
        if order_num in orders:
            continue

        m_date = re.search(r"Datum\s+(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})", txt)
        if not m_date:
            continue

        day = int(m_date.group(1))
        month = MONTH_MAP.get(m_date.group(2).lower(), 1)
        year = int(m_date.group(3))
        order_date = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)

        # Extract total amount
        m_tot = re.search(r"Totaal inclusief btw\s+([\d,]+)", txt)
        total_amount = float(m_tot.group(1).replace(",", ".")) if m_tot else 0.0

        lines = txt.splitlines()
        in_items = False
        items: List[Dict[str, Any]] = []

        for line in lines:
            if "Omschrijving" in line and "Aantal" in line:
                in_items = True
                continue
            if in_items:
                if any(t in line for t in ["Overig", "Statiegeld", "Verpakkingsmateriaal", "Totaal", "Subtotaal", "Betaald"]):
                    if not re.search(r"\b(9%|21%)\b", line):
                        in_items = False
                        continue
                m_item = re.match(r"^\s*(.*?)\s{2,}(\d+)\s+(9%|21%|Geen)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", line)
                if m_item:
                    raw_name = m_item.group(1).strip()
                    qty = int(m_item.group(2))
                    unit_price = float(m_item.group(4).replace(",", "."))
                    total_price = float(m_item.group(6).replace(",", "."))

                    if raw_name.lower() in NON_GROCERY_TERMS:
                        continue

                    norm_name = normalize_item_name(raw_name)
                    item_data = {
                        "raw_name": raw_name,
                        "name": norm_name,
                        "qty": qty,
                        "unit_price": unit_price,
                        "total_price": total_price,
                    }
                    items.append(item_data)
                    item_history[norm_name].append({
                        "date": order_date,
                        "qty": qty,
                        "price": total_price,
                        "order_num": order_num,
                        "raw_name": raw_name,
                    })

        orders[order_num] = {
            "date": order_date,
            "total_amount": total_amount,
            "items": items,
            "file": os.path.basename(pdf_path),
        }

    logger.info(f"Successfully extracted {len(orders)} unique orders and {len(item_history)} unique products.")
    return orders, item_history


def compute_restock_intervals(item_history: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Computes rolling empirical replenishment interval for each product:
      Interval = Delta Days / Units  (average days of household stock per unit)
      Order Frequency = Delta Days / (Orders - 1)
    """
    intervals: Dict[str, Dict[str, Any]] = {}

    for name, history in item_history.items():
        sorted_h = sorted(history, key=lambda x: x["date"])
        total_units = sum(h["qty"] for h in sorted_h)
        unique_dates = sorted(list(set(h["date"] for h in sorted_h)))

        is_dual = any(k in name.lower() for k in DUAL_STORE_KEYWORDS)
        category = infer_category(name)

        if len(unique_dates) > 1:
            delta_days = (unique_dates[-1] - unique_dates[0]).days
            # Average days per unit consumed
            unit_interval = delta_days / total_units if total_units > 0 else 7.0
            # Order interval (how often household repurchases this item)
            order_interval = delta_days / (len(unique_dates) - 1)

            # Clean and bound interval
            eff_interval = max(3.0, round(order_interval, 1))
        else:
            # Single order default heuristic based on category
            if category == models.ItemCategory.FOOD:
                eff_interval = 7.0
            elif category in [models.ItemCategory.HOUSEHOLD, models.ItemCategory.HYGIENE]:
                eff_interval = 28.0
            else:
                eff_interval = 14.0

        intervals[name] = {
            "total_orders": len(unique_dates),
            "total_units": total_units,
            "first_purchased": sorted_h[0]["date"],
            "last_purchased": sorted_h[-1]["date"],
            "restock_interval_days": eff_interval,
            "is_dual_store": is_dual,
            "category": category,
        }

    return intervals


def seed_database():
    """Main execution entrypoint for parsing, resolution, and database seeding."""
    init_db()
    db = SessionLocal()
    ah_client = AHClient()

    ah_dir = "/home/grocerypi/Downloads/ah"
    if not os.path.exists(ah_dir):
        logger.error(f"AH invoice directory {ah_dir} does not exist!")
        return

    orders, item_history = parse_invoices_directory(ah_dir)
    intervals = compute_restock_intervals(item_history)

    # 1. Store or update PurchaseOrders and PurchaseOrderItems
    logger.info("Seeding Purchase Orders...")
    for order_num, odata in orders.items():
        existing_order = db.query(models.PurchaseOrder).filter_by(order_number=order_num).first()
        if not existing_order:
            order_obj = models.PurchaseOrder(
                order_number=order_num,
                order_date=odata["date"],
                source="AH",
                total_amount=odata["total_amount"],
            )
            db.add(order_obj)
            db.flush()

            for item in odata["items"]:
                poi = models.PurchaseOrderItem(
                    order_id=order_obj.id,
                    description=item["name"],
                    quantity=item["qty"],
                    unit_price=item["unit_price"],
                    total_price=item["total_price"],
                )
                db.add(poi)
    db.commit()

    # 2. Seed all unique products into ProductCatalog
    logger.info("Resolving products with AH Mobile API / local cache...")
    catalog_map: Dict[str, models.ProductCatalog] = {}

    for norm_name, meta in intervals.items():
        # Check if already in catalog by name
        prod = db.query(models.ProductCatalog).filter_by(name=norm_name).first()

        if not prod:
            # Query AH API
            ah_data = ah_client.resolve_product(norm_name)
            barcode = ah_data.get("barcode") or generate_fallback_barcode(norm_name)

            # Ensure barcode uniqueness
            existing_bc = db.query(models.ProductCatalog).filter_by(barcode=barcode).first()
            if existing_bc:
                barcode = generate_fallback_barcode(f"{norm_name}-{len(norm_name)}")

            nutri = ah_data.get("nutrition") or {}
            raw_brand = ah_data.get("brand")
            brand = clean_brand(raw_brand, norm_name)
            pkg_size = ah_data.get("package_size")

            prod = models.ProductCatalog(
                barcode=barcode,
                name=norm_name,
                brand=brand,
                category=meta["category"],
                preferred_store=models.PreferredStore.AH,
                is_dual_store=meta["is_dual_store"],
                webshop_id=ah_data.get("webshop_id"),
                package_size=pkg_size,
                energy_kj=nutri.get("energy_kj", 0.0),
                energy_kcal=nutri.get("energy_kcal", 0.0),
                fat_grams=nutri.get("fat_grams", 0.0),
                saturated_fat_grams=nutri.get("saturated_fat_grams", 0.0),
                carbohydrate_grams=nutri.get("carbohydrate_grams", 0.0),
                sugar_grams=nutri.get("sugar_grams", 0.0),
                fiber_grams=nutri.get("fiber_grams", 0.0),
                protein_grams=nutri.get("protein_grams", 0.0),
                salt_grams=nutri.get("salt_grams", 0.0),
            )
            db.add(prod)
            db.flush()
        else:
            # Update dual-store flag
            prod.is_dual_store = meta["is_dual_store"]

        catalog_map[norm_name] = prod

    ah_client.save_cache(force=True)
    db.commit()
    logger.info(f"Catalog populated with {len(catalog_map)} products.")

    # 3. Seed active kitchen inventory
    # Strategy confirmed with user:
    # Seed active inventory with recurring staples (ordered >= 3 times) PLUS all items from the latest order (2026-09-26).
    latest_order_num = max(orders.keys(), key=lambda k: orders[k]["date"])
    latest_order_data = orders[latest_order_num]
    logger.info(f"Latest invoice: {latest_order_num} from {latest_order_data['date'].strftime('%Y-%m-%d')}")

    latest_items_dict = {item["name"]: item["qty"] for item in latest_order_data["items"]}

    inventory_seed_names: Set[str] = set()
    # Add recurring items (>= 3 orders)
    for name, meta in intervals.items():
        if meta["total_orders"] >= 3:
            inventory_seed_names.add(name)

    # Add items from latest order
    for name in latest_items_dict.keys():
        inventory_seed_names.add(name)

    logger.info(f"Seeding {len(inventory_seed_names)} items into active physical inventory...")

    for name in inventory_seed_names:
        prod = catalog_map.get(name)
        if not prod:
            continue

        meta = intervals.get(name, {})
        last_dt = meta.get("last_purchased", latest_order_data["date"])
        interval_days = meta.get("restock_interval_days", 7.0)
        is_dual = meta.get("is_dual_store", False)

        # Quantity: if on latest order, use latest qty; else default to staple baseline
        qty = latest_items_dict.get(name, 1)

        inv_item = db.query(models.InventoryItem).filter_by(product_id=prod.id).first()
        if not inv_item:
            inv_item = models.InventoryItem(
                product_id=prod.id,
                quantity=qty,
                status=models.InventoryStatus.IN_STOCK if qty > 0 else models.InventoryStatus.DEPLETED,
                last_restocked_at=last_dt,
                restock_interval_days=interval_days,
                is_dual_store=is_dual,
            )
            db.add(inv_item)
        else:
            inv_item.quantity = qty
            inv_item.last_restocked_at = last_dt
            inv_item.restock_interval_days = interval_days
            inv_item.is_dual_store = is_dual

    db.commit()
    total_inv = db.query(models.InventoryItem).count()
    logger.info(f"Active Inventory seeded successfully: {total_inv} items in stock.")
    db.close()


if __name__ == "__main__":
    seed_database()

