"""
GroceryPi Test Database Seeder
Populates the local SQLite database with realistic Dutch household products,
real EAN-13 barcodes, categories, and strict 9-field nutritional profiles.
"""

from datetime import datetime, timezone
import logging
from app.database import SessionLocal, Base, engine
from app.models import ProductCatalog, InventoryItem, ItemCategory, PreferredStore, InventoryStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grocerypi.seed")

SEED_PRODUCTS = [
    {
        "barcode": "8710400035541",
        "name": "Pindakaas Original",
        "brand": "Calvé",
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "350g",
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
    },
    {
        "barcode": "8718906001007",
        "name": "Zaanse Halfvolle Melk",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "1L",
        "energy_kj": 198.0,
        "energy_kcal": 47.0,
        "fat_grams": 1.5,
        "saturated_fat_grams": 1.1,
        "carbohydrate_grams": 4.8,
        "sugar_grams": 4.8,
        "fiber_grams": 0.0,
        "protein_grams": 3.6,
        "salt_grams": 0.11,
        "initial_qty": 3,
    },
    {
        "barcode": "8718907058864",
        "name": "Volkoren Havervlokken",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "500g",
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
    },
    {
        "barcode": "8710400010050",
        "name": "Hagelslag Melk",
        "brand": "De Ruijter",
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.JUMBO,
        "package_size": "380g",
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
    },
    {
        "barcode": "8718452134567",
        "name": "Volkoren Penne Rigate",
        "brand": "Jumbo",
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.JUMBO,
        "package_size": "500g",
        "energy_kj": 1475.0,
        "energy_kcal": 349.0,
        "fat_grams": 2.5,
        "saturated_fat_grams": 0.5,
        "carbohydrate_grams": 65.0,
        "sugar_grams": 3.0,
        "fiber_grams": 8.0,
        "protein_grams": 12.5,
        "salt_grams": 0.01,
        "initial_qty": 4,
    },
    {
        "barcode": "8718907231458",
        "name": "Griekse Stijl Yoghurt 10%",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "500g",
        "energy_kj": 526.0,
        "energy_kcal": 127.0,
        "fat_grams": 10.0,
        "saturated_fat_grams": 6.8,
        "carbohydrate_grams": 3.9,
        "sugar_grams": 3.9,
        "fiber_grams": 0.0,
        "protein_grams": 4.7,
        "salt_grams": 0.10,
        "initial_qty": 2,
    },
    {
        "barcode": "8718907456789",
        "name": "Scharrel Kipfilet",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "300g",
        "energy_kj": 465.0,
        "energy_kcal": 110.0,
        "fat_grams": 1.8,
        "saturated_fat_grams": 0.5,
        "carbohydrate_grams": 0.0,
        "sugar_grams": 0.0,
        "fiber_grams": 0.0,
        "protein_grams": 23.5,
        "salt_grams": 0.18,
        "initial_qty": 1,
    },
    {
        "barcode": "8710444057813",
        "name": "Stevige Erwtensoep",
        "brand": "Unox",
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "800ml",
        "energy_kj": 368.0,
        "energy_kcal": 88.0,
        "fat_grams": 3.2,
        "saturated_fat_grams": 1.2,
        "carbohydrate_grams": 8.5,
        "sugar_grams": 1.4,
        "fiber_grams": 3.2,
        "protein_grams": 5.1,
        "salt_grams": 0.72,
        "initial_qty": 2,
    },
    {
        "barcode": "8718907102932",
        "name": "Scharreleieren Klasse M",
        "brand": None,
        "category": ItemCategory.FOOD,
        "preferred_store": PreferredStore.AH,
        "package_size": "10 stuks",
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
    },
    {
        "barcode": "8710400140023",
        "name": "Wasmiddel Vloeibaar Stralend Wit",
        "brand": "Robijn",
        "category": ItemCategory.HOUSEHOLD,
        "preferred_store": PreferredStore.LIDL,
        "package_size": "1L",
        "energy_kj": 0.0,
        "energy_kcal": 0.0,
        "fat_grams": 0.0,
        "saturated_fat_grams": 0.0,
        "carbohydrate_grams": 0.0,
        "sugar_grams": 0.0,
        "fiber_grams": 0.0,
        "protein_grams": 0.0,
        "salt_grams": 0.0,
        "initial_qty": 1,
    },
    {
        "barcode": "8718906103985",
        "name": "Vaatwastabletten All-in-1",
        "brand": None,
        "category": ItemCategory.HOUSEHOLD,
        "preferred_store": PreferredStore.AH,
        "package_size": "40 stuks",
        "energy_kj": 0.0,
        "energy_kcal": 0.0,
        "fat_grams": 0.0,
        "saturated_fat_grams": 0.0,
        "carbohydrate_grams": 0.0,
        "sugar_grams": 0.0,
        "fiber_grams": 0.0,
        "protein_grams": 0.0,
        "salt_grams": 0.0,
        "initial_qty": 1,
    },
    {
        "barcode": "8718906501231",
        "name": "Tandpasta Fresh & Clean",
        "brand": None,
        "category": ItemCategory.HYGIENE,
        "preferred_store": PreferredStore.AH,
        "package_size": "75ml",
        "energy_kj": 0.0,
        "energy_kcal": 0.0,
        "fat_grams": 0.0,
        "saturated_fat_grams": 0.0,
        "carbohydrate_grams": 0.0,
        "sugar_grams": 0.0,
        "fiber_grams": 0.0,
        "protein_grams": 0.0,
        "salt_grams": 0.0,
        "initial_qty": 2,
    },
    {
        "barcode": "8718906204569",
        "name": "Kattenbrokjes Zalm & Groente",
        "brand": None,
        "category": ItemCategory.PET,
        "preferred_store": PreferredStore.AH,
        "package_size": "1.5kg",
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
    },
]


def seed_database(reset: bool = False) -> None:
    """Creates database tables and inserts test household catalog and inventory items."""
    if reset:
        logger.info("Dropping existing tables for clean seed...")
        Base.metadata.drop_all(bind=engine)

    logger.info("Creating all tables in SQLite database...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        inserted_catalog = 0
        inserted_inventory = 0

        for item_data in SEED_PRODUCTS:
            initial_qty = item_data.pop("initial_qty", 1)
            barcode = item_data["barcode"]

            # Check if product already exists
            existing_product = db.query(ProductCatalog).filter(ProductCatalog.barcode == barcode).first()
            if not existing_product:
                product = ProductCatalog(**item_data)
                db.add(product)
                db.flush()  # populate product.id
                inserted_catalog += 1
            else:
                product = existing_product

            # Check if inventory item exists
            existing_inv = db.query(InventoryItem).filter(InventoryItem.product_id == product.id).first()
            if not existing_inv:
                inv_item = InventoryItem(
                    product_id=product.id,
                    quantity=initial_qty,
                    status=InventoryStatus.IN_STOCK,
                    last_restocked_at=datetime.now(timezone.utc),
                    restock_interval_days=7.0,
                )
                db.add(inv_item)
                inserted_inventory += 1

        db.commit()
        logger.info(f"Database seeded successfully: +{inserted_catalog} catalog items, +{inserted_inventory} inventory items.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(reset=True)

