"""
Automated unit tests for the Phase 3 modular backend structure.

This file tests each separated layer of the backend individually:
- ProductRepository: Searching, creating, and making fallback products in the database.
- InventoryRepository & InventoryService: Adding stock on scan, handling physical
  camera scans, updating custom restock days, deleting items, and logging scan history.
- NutritionService: Calculating average Nutri-Score grades and counting vegan and
  vegetarian items without double-counting.
- PredictionEngine: Sorting low-stock items into Albert Heijn, Jumbo, and Lidl queues.
- Scanner, Products, and Auth Routers: Checking camera controls, product search,
  and hashed-password user login.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password, verify_password
from app.clients.store_gateway import IStoreGateway
from app.database import Base, get_db
from app.db.repositories.inventory_repository import InventoryRepository
from app.db.repositories.product_repository import ProductRepository
from app.main import app
from app.models import (
    InventoryItem,
    InventoryStatus,
    ItemCategory,
    PreferredStore,
    ProductCatalog,
)
from app.schemas import InventoryItemUpdate, ProductCatalogCreate
from app.services.ah_client import AHClient
from app.services.inventory.inventory import InventoryService
from app.services.nutrition.nutrition import NutritionService
from app.services.prediction.prediction import PredictionEngine

# Create an isolated in-memory test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Provides a clean test database session for API calls."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_phase3_db():
    """Sets up fresh tables and connects the test database before each test."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_product_repository_crud_and_fallback():
    """Checks that ProductRepository can create, find, search, and make fallback products."""
    db = TestingSessionLocal()
    try:
        payload = ProductCatalogCreate(
            barcode="8710000000111",
            name="Volkoren Brood",
            brand="Bakker",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.JUMBO,
            package_size="800g",
            nutriscore="A",
            is_vegetarian=True,
            is_vegan=True,
            energy_kcal=240.0,
            protein_grams=9.5,
            fiber_grams=7.2,
        )
        created = ProductRepository.create(db, payload)
        assert created.id is not None
        assert created.name == "Volkoren Brood"

        # Find by barcode
        found = ProductRepository.get_by_barcode(db, "8710000000111")
        assert found is not None
        assert found.preferred_store == PreferredStore.JUMBO

        # Search by keyword and store filter
        results = ProductRepository.list_products(db, q="Brood", preferred_store=PreferredStore.JUMBO)
        assert len(results) == 1

        # Create fallback placeholder product for an unknown physical barcode
        fallback = ProductRepository.create_fallback(db, "8719998887776")
        assert fallback.barcode == "8719998887776"
        assert "Scanned Item" in fallback.name
        assert fallback.preferred_store == PreferredStore.OTHER
    finally:
        db.close()


def test_inventory_service_fallback_and_delete_flow():
    """
    Checks that InventoryService creates a placeholder item when a physical barcode
    is not found online, records the scan in history, and allows deleting the item.
    """
    db = TestingSessionLocal()
    try:
        # Use a custom service whose online lookup always returns None (simulating an unknown item)
        service = InventoryService(barcode_resolver=lambda code, session: None)

        scan_res = service.ingest_scan(
            db=db,
            barcode="8712345678905",
            device_info="Test Scanner",
            allow_fallback_creation=True,
        )
        assert scan_res.scan_status == "SUCCESS"
        assert scan_res.product is not None
        assert scan_res.inventory_item is not None
        assert scan_res.inventory_item.quantity == 1

        # Check that the scan was recorded in recent scan logs
        logs = service.get_recent_scans(db, limit=5)
        assert len(logs) == 1
        assert logs[0].raw_barcode == "8712345678905"

        # Update quantity and custom restock interval
        updated = service.update_item(
            db,
            scan_res.inventory_item.id,
            InventoryItemUpdate(quantity=0, manual_interval_override=14.0),
        )
        assert updated.quantity == 0
        assert updated.status == InventoryStatus.DEPLETED
        assert updated.manual_interval_override == 14.0

        # Delete the item and confirm it is gone
        service.delete_item(db, updated.id)
        remaining = service.list_inventory(db)
        assert len(remaining) == 0
    finally:
        db.close()


def test_nutrition_service_vegan_vegetarian_and_nutriscore():
    """
    Checks that NutritionService counts vegan and vegetarian items separately
    (no double-counting) and calculates the weighted average Nutri-Score grade.
    """
    db = TestingSessionLocal()
    try:
        # Product 1: Vegan item with Nutri-Score A (2 units)
        p_vegan = ProductCatalog(
            barcode="8710000000201",
            name="Haverdrink",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.AH,
            nutriscore="A",
            is_vegan=True,
            is_vegetarian=True,
            protein_grams=1.0,
            energy_kcal=45.0,
        )
        # Product 2: Vegetarian (non-vegan) item with Nutri-Score C (1 unit)
        p_veg = ProductCatalog(
            barcode="8710000000202",
            name="Goudse Kaas",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.AH,
            nutriscore="C",
            is_vegan=False,
            is_vegetarian=True,
            protein_grams=25.0,
            energy_kcal=350.0,
        )
        db.add_all([p_vegan, p_veg])
        db.commit()

        db.add_all([
            InventoryItem(product_id=p_vegan.id, quantity=2, status=InventoryStatus.IN_STOCK),
            InventoryItem(product_id=p_veg.id, quantity=1, status=InventoryStatus.IN_STOCK),
        ])
        db.commit()

        nutrition_svc = NutritionService()
        summary = nutrition_svc.get_pantry_summary(db)

        assert summary["total_items_counted"] == 3
        assert summary["total_vegan_items"] == 2
        assert summary["total_vegetarian_items"] == 1
        assert summary["total_protein_grams"] == 27.0
        assert summary["nutriscore_counts"]["A"] == 2
        assert summary["nutriscore_counts"]["C"] == 1
        assert summary["average_nutriscore"] in ["A", "B"]
    finally:
        db.close()


def test_prediction_engine_multi_store_queues():
    """
    Checks that PredictionEngine groups low-stock items into the right supermarket
    lists (AH, Jumbo, and Lidl).
    """
    db = TestingSessionLocal()
    try:
        p_ah = ProductCatalog(
            barcode="8710000000301",
            name="Halfvolle Melk",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.AH,
        )
        p_jumbo = ProductCatalog(
            barcode="8710000000302",
            name="Afwasmiddel",
            category=ItemCategory.HOUSEHOLD,
            preferred_store=PreferredStore.JUMBO,
            is_dual_store=True,
        )
        p_lidl = ProductCatalog(
            barcode="8710000000303",
            name="Volkoren Havermout",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.LIDL,
        )
        db.add_all([p_ah, p_jumbo, p_lidl])
        db.commit()

        db.add_all([
            InventoryItem(product_id=p_ah.id, quantity=1, status=InventoryStatus.IN_STOCK),
            InventoryItem(product_id=p_jumbo.id, quantity=0, status=InventoryStatus.DEPLETED, is_dual_store=True),
            InventoryItem(product_id=p_lidl.id, quantity=1, status=InventoryStatus.IN_STOCK),
        ])
        db.commit()

        engine_svc = PredictionEngine()
        suggestions = engine_svc.get_cart_replenishment_suggestions(db)

        queues_by_id = {q.id: q for q in suggestions.queues}
        assert len(queues_by_id["AH"].items) == 1
        assert len(queues_by_id["Jumbo"].items) == 1
        assert len(queues_by_id["Lidl"].items) == 1
        assert queues_by_id["Jumbo"].items[0].urgency == "high"
    finally:
        db.close()


def test_products_scanner_and_auth_endpoints():
    """
    Checks the /products, /scanner, and /auth API routes, including password
    hashing and user token login.
    """
    # 1. Check password hashing helper directly
    hashed = hash_password("kitchenSecret123")
    assert hashed != "kitchenSecret123"
    assert verify_password("kitchenSecret123", hashed) is True
    assert verify_password("wrongPassword", hashed) is False

    # 2. Register and log in via /auth endpoints
    reg_res = client.post(
        "/auth/register",
        json={"username": "cinna", "email": "cinna@example.com", "password": "kitchenSecret123"},
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]

    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "cinna"

    # 3. Create, fetch, and edit a product via /products endpoints
    prod_res = client.post(
        "/products",
        json={
            "barcode": "8710000000401",
            "name": "Biologische Eieren",
            "category": "Food",
            "preferred_store": "AH",
            "protein_grams": 13.0,
        },
    )
    assert prod_res.status_code == 201
    get_prod = client.get("/products/8710000000401")
    assert get_prod.status_code == 200
    assert get_prod.json()["name"] == "Biologische Eieren"

    patch_prod = client.patch(
        "/products/8710000000401",
        json={
            "name": "Vrije Uitloop Eieren",
            "package_size": "12 pack",
            "preferred_store": "Jumbo",
        },
    )
    assert patch_prod.status_code == 200
    assert patch_prod.json()["name"] == "Vrije Uitloop Eieren"
    assert patch_prod.json()["package_size"] == "12 pack"
    assert patch_prod.json()["preferred_store"] == "Jumbo"

    # 4. Check /scanner status, hardware detection states, and camera FPS vs decode throttle interval
    assert issubclass(AHClient, IStoreGateway)
    scan_status = client.get("/scanner/status")
    assert scan_status.status_code == 200
    status_data = scan_status.json()
    assert "sensor" in status_data
    assert "hardware_detected" in status_data
    assert "state" in status_data
    assert "sensor_short_name" in status_data
    assert status_data["preview_fps"] == 12
    assert 0.5 <= status_data["scan_interval_seconds"] <= 1.0

    # 5. Directly test Picamera2BarcodeScanner decode throttling & health status states
    from app.services.scanner.scanner import Picamera2BarcodeScanner
    cam_scanner = Picamera2BarcodeScanner(fps=12, scan_interval_seconds=0.75)
    assert cam_scanner.fps == 12
    assert cam_scanner.scan_interval_seconds == 0.75
    assert cam_scanner.get_health_status(now=100.0)["state"] == "not_detected"
    cam_scanner._hardware_detected = True
    cam_scanner._is_running = True
    cam_scanner._last_frame_time = 99.5
    assert cam_scanner.get_health_status(now=100.0)["state"] == "online"
    assert cam_scanner.get_health_status(now=103.5)["state"] == "lagging"
    cam_scanner._is_running = False
    assert cam_scanner.get_health_status(now=103.5)["state"] == "offline"
    # First check at t=100.0s should trigger a decode
    assert cam_scanner._should_trigger_decode(now=100.0) is True
    # Next frame 83ms later (12 FPS -> t=100.083s) should skip decode so preview stays fast
    assert cam_scanner._should_trigger_decode(now=100.083) is False
    # Frame after 0.75s has passed (t=100.80s) should trigger the next decode
    assert cam_scanner._should_trigger_decode(now=100.80) is True


def test_barcode_checksum_validation_and_dutch_english_off_selection():
    """
    Checks that:
    1. Valid retail EAN-13 barcodes pass GS1 Modulo-10 check-digit validation,
       while motion-blurred wrong-check-digit or short numbers are rejected.
    2. Unrecognized barcodes are blocked from entering the database unless the
       user explicitly confirms adding them (confirm_unknown=True).
    3. Open Food Facts lookup strictly selects Dutch (NL) or English (EN) names
       and ignores German or Spanish titles.
    """
    from app.services.ah_client import select_dutch_or_english_name
    from app.services.scanner import is_valid_retail_barcode

    # 1. GS1 Modulo-10 Check-Digit Validation
    assert is_valid_retail_barcode("8710400035541") is True
    assert is_valid_retail_barcode("8710400035542") is False  # 1 digit off from motion blur
    assert is_valid_retail_barcode("1428") is False  # Short non-retail number
    assert is_valid_retail_barcode("ABC1234567890") is False

    # 2. Unrecognized barcode requires confirmation before entering database
    unconfirmed_res = client.post(
        "/inventory/scan",
        json={"barcode": "8719991112223", "confirm_unknown": False},
    )
    assert unconfirmed_res.status_code == 200
    assert unconfirmed_res.json()["scan_status"] == "UNKNOWN_BARCODE"
    assert unconfirmed_res.json()["product"] is None

    confirmed_res = client.post(
        "/inventory/scan",
        json={"barcode": "8719991112223", "confirm_unknown": True},
    )
    assert confirmed_res.status_code == 200
    assert confirmed_res.json()["scan_status"] == "SUCCESS"
    assert confirmed_res.json()["product"]["barcode"] == "8719991112223"

    # 3. Open Food Facts Dutch / English language filtering
    off_german_default = {
        "lang": "de",
        "product_name": "Erdnussbutter Cremig",
        "product_name_de": "Erdnussbutter Cremig",
        "product_name_nl": "Pindakaas Romig",
        "product_name_en": "Creamy Peanut Butter",
    }
    assert select_dutch_or_english_name(off_german_default) == "Pindakaas Romig"

    off_spanish_with_english = {
        "lang": "es",
        "product_name": "Barrita de cereales con miel",
        "product_name_es": "Barrita de cereales con miel",
        "product_name_en": "Honey Cereal Bar",
    }
    assert select_dutch_or_english_name(off_spanish_with_english) == "Honey Cereal Bar"

    off_foreign_only = {
        "lang": "es",
        "product_name": "Galletas de avena",
        "product_name_es": "Galletas de avena",
    }
    assert select_dutch_or_english_name(off_foreign_only) is None


def test_checkin_midnight_batch_auto_depletion_and_cart_sync():
    """
    Tests Epic 3.4 ("Items IN" Depletion, Midnight Replenishment & Cart Sync Lifecycle):
    1. User Story 3.4.1: Multiple scans on the same calendar day increment quantity
       (1 -> 2 -> 3), while a scan on a new calendar day (after 00:00 midnight)
       treats the previous batch as finished, updates restock_interval_days, and
       resets quantity to 1 for the new batch.
    2. User Story 3.4.2: Automatic depletion marks items past their restock interval
       (or 30-day shelf cap) as DEPLETED (quantity = 0) while preserving their
       learned restock_interval_days.
    3. User Story 3.4.3: POST /inventory/cart/sync/{store} marks recommended items
       for that store as DEPLETED (quantity = 0) so they leave the active Dashboard
       visually while staying in Cart Suggestions until physically scanned IN again.
    """
    from datetime import datetime, timedelta, timezone

    db = TestingSessionLocal()
    try:
        milk = ProductCatalog(
            barcode="8710400000013",
            name="Halfvolle Melk",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.AH,
        )
        db.add(milk)
        db.commit()
        db.refresh(milk)

        # 1. First scan creates 1 unit in stock
        item = InventoryRepository.upsert_stock_on_scan(db, milk.id)
        assert item.quantity == 1
        assert item.status == InventoryStatus.IN_STOCK

        # Second scan on the SAME calendar day increments batch count to 2
        item = InventoryRepository.upsert_stock_on_scan(db, milk.id)
        assert item.quantity == 2

        # Simulate 5 days passing (across midnight into a new calendar day)
        five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
        item.last_restocked_at = five_days_ago
        item.restock_interval_days = 7.0
        db.commit()

        # Scanning on the new calendar day resets quantity to 1 (new batch) and updates interval
        item = InventoryRepository.upsert_stock_on_scan(db, milk.id)
        assert item.quantity == 1
        assert item.status == InventoryStatus.IN_STOCK
        # Rolling average: 0.7 * 7.0 + 0.3 * 5.0 = 6.4 days
        assert 6.0 <= item.restock_interval_days <= 6.6

        # 2. Automatic depletion after restock interval (or 30-day cap) elapses
        item.last_restocked_at = datetime.now(timezone.utc) - timedelta(days=8)
        db.commit()

        depleted_count = InventoryRepository.apply_auto_depletion(db)
        assert depleted_count == 1
        db.refresh(item)
        assert item.status == InventoryStatus.DEPLETED
        assert item.quantity == 0
        # Learned interval is preserved even when depleted
        assert 6.0 <= item.restock_interval_days <= 6.6

        # 3. Scanning the depleted item back in replenishes it to quantity = 1
        item = InventoryRepository.upsert_stock_on_scan(db, milk.id)
        assert item.quantity == 1
        assert item.status == InventoryStatus.IN_STOCK

        # 4. Syncing the AH Cart queue marks recommended AH items as DEPLETED (0 units)
        # while keeping them in Cart Suggestions until scanned IN again
        sync_res = client.post("/inventory/cart/sync/AH")
        assert sync_res.status_code == 200
        assert sync_res.json()["synced_count"] >= 1

        db.refresh(item)
        assert item.status == InventoryStatus.DEPLETED
        assert item.quantity == 0

        suggestions_res = client.get("/inventory/cart/suggestions")
        assert suggestions_res.status_code == 200
        ah_queue = next(q for q in suggestions_res.json()["queues"] if q["id"] == "AH")
        assert any(i["name"] == "Halfvolle Melk" for i in ah_queue["items"])
        assert any("synced / depleted" in i["subtext"] for i in ah_queue["items"])

        # 5. User Story 3.4.5: Auto-detect frozen items from AH ('Diepvries') and OFF ('en:frozen-foods'),
        # and exempt Frozen & Non-Food items from the 30-day shelf cap
        from app.services.ah_client import detect_is_frozen

        assert detect_is_frozen(main_cat="Diepvries", title="Blauwe bessen") is True
        assert detect_is_frozen(categories_tags=["en:frozen-foods", "en:frozen-vegetables"]) is True
        assert detect_is_frozen(main_cat="Zuivel", title="Halfvolle melk") is False

        frozen_berries = ProductCatalog(
            barcode="8710400000099",
            name="Diepvries Aardbeien",
            category=ItemCategory.FOOD,
            preferred_store=PreferredStore.AH,
            is_frozen=True,
        )
        dish_soap = ProductCatalog(
            barcode="8710400000082",
            name="Afwasmiddel Citroen",
            category=ItemCategory.HOUSEHOLD,
            preferred_store=PreferredStore.JUMBO,
            is_frozen=False,
        )
        db.add_all([frozen_berries, dish_soap])
        db.commit()
        db.refresh(frozen_berries)
        db.refresh(dish_soap)

        # Stock both items 32 days ago with a 60-day restock interval
        thirty_two_days_ago = datetime.now(timezone.utc) - timedelta(days=32)
        frozen_inv = InventoryItem(
            product_id=frozen_berries.id,
            quantity=1,
            status=InventoryStatus.IN_STOCK,
            last_restocked_at=thirty_two_days_ago,
            restock_interval_days=60.0,
        )
        soap_inv = InventoryItem(
            product_id=dish_soap.id,
            quantity=1,
            status=InventoryStatus.IN_STOCK,
            last_restocked_at=thirty_two_days_ago,
            restock_interval_days=60.0,
        )
        db.add_all([frozen_inv, soap_inv])
        db.commit()

        # Running apply_auto_depletion at 32 days must NOT deplete the frozen berries or dish soap
        InventoryRepository.apply_auto_depletion(db)
        db.refresh(frozen_inv)
        db.refresh(soap_inv)
        assert frozen_inv.status == InventoryStatus.IN_STOCK
        assert frozen_inv.quantity == 1
        assert soap_inv.status == InventoryStatus.IN_STOCK
        assert soap_inv.quantity == 1

        # 6. Epic 4.1: Polymorphic IStoreGateway implementations & OFF Store Auto-Detection
        from app.clients.ah_gateway import AHStoreGateway, JumboStoreGateway
        from app.clients.off_client import OpenFoodFactsClient
        from app.services.ah_client import infer_preferred_store_from_off

        assert issubclass(AHStoreGateway, IStoreGateway)
        assert issubclass(JumboStoreGateway, IStoreGateway)
        assert issubclass(OpenFoodFactsClient, IStoreGateway)

        assert (
            infer_preferred_store_from_off({"brands": "Milbona", "stores_tags": []}, "Milbona")
            == PreferredStore.LIDL
        )
        assert (
            infer_preferred_store_from_off({"brands": "Jumbo", "stores": "Jumbo"}, "Jumbo")
            == PreferredStore.JUMBO
        )
        ah_gw = AHStoreGateway()
        sync_payload = ah_gw.sync_cart([{"name": "Halfvolle Melk"}])
        assert sync_payload["store"] == "AH"
        assert sync_payload["synced_count"] == 1
    finally:
        db.close()


