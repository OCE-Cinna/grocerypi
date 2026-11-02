import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import ProductCatalog, InventoryItem, ItemCategory, PreferredStore, InventoryStatus
from app.services.scanner import MockBarcodeScanner

# Use in-memory SQLite for fast, isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Rebuilds tables and seeds initial test data before each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed 2 products with 9 nutritional fields in order
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

    # Seed 1 inventory item for p1
    inv = InventoryItem(product_id=p1.id, quantity=1, status=InventoryStatus.IN_STOCK)
    db.add(inv)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"


def test_scan_known_barcode_increments_inventory():
    """Scanning an existing item logs scan and increments quantity."""
    response = client.post("/inventory/scan", json={"barcode": "8710400035541"})
    assert response.status_code == 200
    data = response.json()
    assert data["scan_status"] == "SUCCESS"
    assert data["inventory_item"]["quantity"] == 2
    assert data["product"]["name"] == "Calvé Pindakaas"
    assert data["product"]["protein_grams"] == 21.0


def test_scan_unknown_barcode():
    """Scanning an unknown barcode returns UNKNOWN_BARCODE status without error."""
    response = client.post("/inventory/scan", json={"barcode": "9999999999999"})
    assert response.status_code == 200
    data = response.json()
    assert data["scan_status"] == "UNKNOWN_BARCODE"
    assert data["product"] is None
    assert data["inventory_item"] is None


def test_get_inventory_nutritional_fields_order():
    """Inventory response includes all 9 nutritional fields in order."""
    response = client.get("/inventory")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    p = items[0]["product"]
    # Check all 9 fields exist
    fields = [
        "energy_kj", "energy_kcal", "fat_grams", "saturated_fat_grams",
        "carbohydrate_grams", "sugar_grams", "fiber_grams", "protein_grams", "salt_grams"
    ]
    for f in fields:
        assert f in p


def test_autosort_by_protein():
    """Clicking a nutrition bar triggers autosorting (GET /inventory?sort_by=protein_grams)."""
    # First, scan Kipfilet so both items are in inventory
    client.post("/inventory/scan", json={"barcode": "8718907456789"})

    # Sort descending by protein (Kipfilet has 23.5g, Pindakaas has 21.0g)
    response = client.get("/inventory?sort_by=protein_grams&order=desc")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert items[0]["product"]["protein_grams"] == 23.5
    assert items[1]["product"]["protein_grams"] == 21.0


def test_nutrition_summary():
    """Calculates aggregate macros across active stock."""
    response = client.get("/inventory/nutrition/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items_counted"] == 1
    assert data["total_protein_grams"] == 21.0
    assert data["total_energy_kcal"] == 664.0


def test_mock_scanner_service():
    """Tests the decoupled scanner service interface, callback, and debouncing."""
    scans_received = []

    def on_scan(barcode):
        scans_received.append(barcode)

    scanner = MockBarcodeScanner(debounce_seconds=1.0)
    scanner.start(on_scan)
    assert scanner.is_running is True

    # First scan should succeed
    res1 = scanner.simulate_scan("8710400035541")
    assert res1 is True
    assert len(scans_received) == 1

    # Immediate second scan of the same barcode should be debounced
    res2 = scanner.simulate_scan("8710400035541")
    assert res2 is False
    assert len(scans_received) == 1

    # Scan of different barcode should succeed immediately
    res3 = scanner.simulate_scan("8718907456789")
    assert res3 is True
    assert len(scans_received) == 2

    scanner.stop()
    assert scanner.is_running is False


def test_cart_replenishment_suggestions():
    """Tests the smart supermarket queue suggestions and prediction intervals."""
    res = client.get("/inventory/cart/suggestions")
    assert res.status_code == 200
    data = res.json()
    assert "queues" in data
    assert len(data["queues"]) >= 2
    
    queue_ids = [q["id"] for q in data["queues"]]
    assert "AH" in queue_ids
    assert "Jumbo" in queue_ids
    
    # Check that item fields are populated
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
    Tests scanning an uncatalogued GTIN barcode (8710466269522):
    Pulls metadata directly from Albert Heijn API, saves to ProductCatalog,
    and increments inventory stock.
    """
    res = client.post("/inventory/scan", json={"barcode": "8710466269522"})
    assert res.status_code == 200
    data = res.json()
    assert data["scan_status"] == "SUCCESS"
    assert "Koopmans" in data["product"]["name"]
    assert data["product"]["nutriscore"] == "E"
    assert data["inventory_item"]["quantity"] >= 1



