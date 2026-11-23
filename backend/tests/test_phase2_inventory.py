"""
Automated backend tests for GroceryPi.

This file tests the core features of the backend using a temporary in-memory
database so the real kitchen database is not changed:
- Checking if the server is online.
- Scanning known, unknown, and online Albert Heijn barcodes.
- Checking that all 9 nutrition values are returned and can be used to sort items.
- Calculating total pantry nutrition and shopping cart restock suggestions.
- Testing the barcode scanner cooldown (debouncing) and modular service updates.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import InventoryItem, InventoryStatus, ItemCategory, PreferredStore, ProductCatalog
from app.services.scanner import MockBarcodeScanner

# Use a temporary in-memory SQLite database so tests run quickly and cleanly
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Provides a temporary test database connection during automated tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Creates fresh database tables and adds 2 sample products before each test runs."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Add 2 test products with all 9 European nutrition values
    p1 = ProductCatalog(
        barcode="8710400035541",
        name="Calvé Pindakaas",
        brand="Calvé",
        category=ItemCategory.FOOD,
        preferred_store=PreferredStore.AH,
        package_size="350g",
        energy_kj=2773.0,
        energy_kcal=664.0,
        fat_grams=58.0,
        saturated_fat_grams=8.5,
        carbohydrate_grams=11.0,
        sugar_grams=6.4,
        fiber_grams=6.6,
        protein_grams=21.0,
        salt_grams=0.55,
    )
    p2 = ProductCatalog(
        barcode="8718907456789",
        name="Scharrel Kipfilet",
        brand="Albert Heijn",
        category=ItemCategory.FOOD,
        preferred_store=PreferredStore.AH,
        package_size="300g",
        energy_kj=465.0,
        energy_kcal=110.0,
        fat_grams=1.8,
        saturated_fat_grams=0.5,
        carbohydrate_grams=0.0,
        sugar_grams=0.0,
        fiber_grams=0.0,
        protein_grams=23.5,
        salt_grams=0.18,
    )
    db.add_all([p1, p2])
    db.commit()

    # Put 1 jar of peanut butter in the starting kitchen inventory
    inv = InventoryItem(product_id=p1.id, quantity=1, status=InventoryStatus.IN_STOCK)
    db.add(inv)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def test_health_check():
    """Checks that the main API endpoint responds and reports that the server is ok."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"


def test_scan_known_barcode_increments_inventory():
    """Checks that scanning an item already in stock increases its quantity from 1 to 2."""
    response = client.post("/inventory/scan", json={"barcode": "8710400035541"})
    assert response.status_code == 200
    data = response.json()
    assert data["scan_status"] == "SUCCESS"
    assert data["inventory_item"]["quantity"] == 2
    assert data["product"]["name"] == "Calvé Pindakaas"
    assert data["product"]["protein_grams"] == 21.0


def test_scan_unknown_barcode():
    """Checks that scanning a test barcode that does not exist returns UNKNOWN_BARCODE safely."""
    response = client.post("/inventory/scan", json={"barcode": "9999999999999"})
    assert response.status_code == 200
    data = response.json()
    assert data["scan_status"] == "UNKNOWN_BARCODE"
    assert data["product"] is None
    assert data["inventory_item"] is None


def test_get_inventory_nutritional_fields_order():
    """Checks that the inventory list includes all 9 nutrition values for each product."""
    response = client.get("/inventory")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    p = items[0]["product"]
    fields = [
        "energy_kj", "energy_kcal", "fat_grams", "saturated_fat_grams",
        "carbohydrate_grams", "sugar_grams", "fiber_grams", "protein_grams", "salt_grams",
    ]
    for f in fields:
        assert f in p


def test_autosort_by_protein():
    """Checks that sorting the inventory by protein puts the highest-protein item first."""
    client.post("/inventory/scan", json={"barcode": "8718907456789"})

    response = client.get("/inventory?sort_by=protein_grams&order=desc")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert items[0]["product"]["protein_grams"] == 23.5
    assert items[1]["product"]["protein_grams"] == 21.0


def test_nutrition_summary():
    """Checks that the nutrition summary correctly adds up calories and protein in stock."""
    response = client.get("/inventory/nutrition/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items_counted"] == 1
    assert data["total_protein_grams"] == 21.0
    assert data["total_energy_kcal"] == 664.0


def test_mock_scanner_service():
    """Checks that the scanner service reads barcodes and ignores accidental double-scans."""
    scans_received = []

    def on_scan(barcode):
        scans_received.append(barcode)

    scanner = MockBarcodeScanner(debounce_seconds=1.0)
    scanner.start(on_scan)
    assert scanner.is_running is True

    # First scan should be accepted
    res1 = scanner.simulate_scan("8710400035541")
    assert res1 is True
    assert len(scans_received) == 1

    # Immediate second scan of the same barcode should be ignored (debounced)
    res2 = scanner.simulate_scan("8710400035541")
    assert res2 is False
    assert len(scans_received) == 1

    # Scanning a different product barcode should work right away
    res3 = scanner.simulate_scan("8718907456789")
    assert res3 is True
    assert len(scans_received) == 2

    scanner.stop()
    assert scanner.is_running is False


def test_cart_replenishment_suggestions():
    """Checks that the shopping cart prediction engine creates store lists for AH and Jumbo."""
    res = client.get("/inventory/cart/suggestions")
    assert res.status_code == 200
    data = res.json()
    assert "queues" in data
    assert len(data["queues"]) >= 2

    queue_ids = [q["id"] for q in data["queues"]]
    assert "AH" in queue_ids
    assert "Jumbo" in queue_ids

    ah_queue = next(q for q in data["queues"] if q["id"] == "AH")
    assert ah_queue["title"].startswith("AH ·")
    assert len(ah_queue["items"]) > 0
    first_item = ah_queue["items"][0]
    assert "name" in first_item
    assert "quantity_text" in first_item
    assert "effective_interval_days" in first_item
    assert "subtext" in first_item


def test_ah_api_product_auto_resolution():
    """
    Checks that scanning a real barcode not yet in our local database looks up
    the product from the Albert Heijn API, saves it, and adds 1 unit to stock.
    """
    res = client.post("/inventory/scan", json={"barcode": "8710466269522"})
    assert res.status_code == 200
    data = res.json()
    assert data["scan_status"] == "SUCCESS"
    assert "Koopmans" in data["product"]["name"]
    assert data["product"]["nutriscore"] == "E"
    assert data["inventory_item"]["quantity"] >= 1


def test_modular_services_and_interval_override_update():
    """
    Checks that the modular inventory and nutrition services work properly,
    updating an item's custom restock days saves to the database, and the
    camera scanner status endpoints respond as expected.
    """
    from app.clients.store_gateway import IStoreGateway
    from app.services.ah_client import AHClient
    from app.services.inventory.inventory import InventoryService, inventory_service
    from app.services.nutrition.nutrition import NutritionService, nutrition_service

    assert isinstance(inventory_service, InventoryService)
    assert isinstance(nutrition_service, NutritionService)
    assert issubclass(AHClient, IStoreGateway)

    # Check that updating quantity, custom restock days, and dual-store works
    inv_res = client.get("/inventory")
    assert inv_res.status_code == 200
    first_item = inv_res.json()[0]
    item_id = first_item["id"]

    patch_res = client.patch(
        f"/inventory/{item_id}",
        json={"quantity": 4, "manual_interval_override": 12.5, "is_dual_store": True},
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["quantity"] == 4
    assert updated["manual_interval_override"] == 12.5
    assert updated["is_dual_store"] is True

    # Check the extracted camera scanner status endpoints
    status_res = client.get("/scanner/status")
    assert status_res.status_code == 200
    assert "running" in status_res.json()

    event_res = client.get("/scanner/latest-event")
    assert event_res.status_code == 200
    assert "scan_id" in event_res.json()
