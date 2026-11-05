import React, { useState, useEffect, useCallback, useRef } from "react";
import Navbar from "./components/Navbar";
import DashboardPage from "./pages/DashboardPage";
import CartPage from "./pages/CartPage";
import NutritionPage from "./pages/NutritionPage";
import ScanFeedbackOverlay from "./components/ScanFeedbackOverlay";
import DeleteConfirmModal from "./components/DeleteConfirmModal";
import ScanModal from "./components/ScanModal";
import api from "./api/client";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [items, setItems] = useState([]);
  const [sampleProducts, setSampleProducts] = useState([]);
  const [nutritionSummary, setNutritionSummary] = useState(null);
  const [activeSortNutrient, setActiveSortNutrient] = useState(null);

  // Modals
  const [scanFeedbackEvent, setScanFeedbackEvent] = useState(null);
  const [deleteModalItem, setDeleteModalItem] = useState(null);
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [scannerStatus, setScannerStatus] = useState("demo");

  // Fetch inventory from backend
  const fetchInventory = useCallback(async (sortNutrient = null) => {
    try {
      let url = "/inventory";
      if (sortNutrient?.key) {
        url += `?sort_by=${sortNutrient.key}&order=desc`;
      }
      const res = await api.get(url);
      setItems(res.data);
    } catch (err) {
      console.error("Failed to fetch inventory:", err);
    }
  }, []);

  // Fetch catalog & nutrition summary
  const fetchAuxData = useCallback(async () => {
    try {
      const [prodRes, nutRes, scanRes] = await Promise.allSettled([
        api.get("/products?limit=25"),
        api.get("/inventory/nutrition/summary"),
        api.get("/scanner/status"),
      ]);
      if (prodRes.status === "fulfilled") setSampleProducts(prodRes.value.data);
      if (nutRes.status === "fulfilled") setNutritionSummary(nutRes.value.data);
      if (scanRes.status === "fulfilled") {
        setScannerStatus(scanRes.value.data.running ? "hardware active" : "demo");
      }
    } catch (err) {
      console.error("Auxiliary data fetch error:", err);
    }
  }, []);

  const lastProcessedScanIdRef = useRef(0);

  useEffect(() => {
    fetchInventory(activeSortNutrient);
    fetchAuxData();
  }, [fetchInventory, fetchAuxData, activeSortNutrient]);

  // Listen for hardware barcode scans from Camera Module v3 loop
  useEffect(() => {
    // Prime the latest scan ID so previous scans aren't re-triggered on load
    api.get("/scanner/latest-event")
      .then((res) => {
        if (res.data?.scan_id) {
          lastProcessedScanIdRef.current = res.data.scan_id;
        }
      })
      .catch(() => {});

    const interval = setInterval(async () => {
      try {
        const res = await api.get("/scanner/latest-event");
        const event = res.data;
        if (event && event.scan_id && event.scan_id > lastProcessedScanIdRef.current) {
          lastProcessedScanIdRef.current = event.scan_id;
          if (event.scan_status === "SUCCESS") {
            setScanFeedbackEvent(event);
            setIsScanModalOpen(false);
            fetchInventory(activeSortNutrient);
            fetchAuxData();
          } else if (event.scan_status === "UNKNOWN_BARCODE") {
            alert(event.message || `Barcode '${event.barcode}' not in catalog.`);
          }
        }
      } catch (err) {
        // Quietly ignore polling blips
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [fetchInventory, fetchAuxData, activeSortNutrient]);

  // Handle barcode scan ingestion
  const handleScanBarcode = async (barcode) => {
    try {
      const res = await api.post("/inventory/scan", {
        barcode: barcode.trim(),
        device_info: "Raspberry Pi Kiosk Interface",
      });

      if (res.data.scan_status === "SUCCESS") {
        setScanFeedbackEvent(res.data);
        fetchInventory(activeSortNutrient);
        fetchAuxData();
      } else {
        alert(res.data.message || `Barcode '${barcode}' not in catalog.`);
      }
    } catch (err) {
      console.error("Scan error:", err);
      alert("Failed to process scan event.");
    }
  };

  // Undo scan action
  const handleUndoScan = async (event) => {
    try {
      const invId = event.inventory_item?.id;
      if (invId) {
        const currentQty = event.inventory_item.quantity;
        if (currentQty <= 1) {
          await api.delete(`/inventory/${invId}`);
        } else {
          await api.patch(`/inventory/${invId}`, { quantity: currentQty - 1 });
        }
      }
      setScanFeedbackEvent(null);
      fetchInventory(activeSortNutrient);
      fetchAuxData();
    } catch (err) {
      console.error("Undo error:", err);
    }
  };

  // Increment item quantity (+)
  const handleIncrement = async (item) => {
    try {
      await api.patch(`/inventory/${item.id}`, { quantity: item.quantity + 1 });
      fetchInventory(activeSortNutrient);
      fetchAuxData();
    } catch (err) {
      console.error("Increment error:", err);
    }
  };

  // Decrement item quantity (-)
  const handleDecrement = async (item) => {
    if (item.quantity <= 1) {
      setDeleteModalItem(item);
      return;
    }
    try {
      await api.patch(`/inventory/${item.id}`, { quantity: item.quantity - 1 });
      fetchInventory(activeSortNutrient);
      fetchAuxData();
    } catch (err) {
      console.error("Decrement error:", err);
    }
  };

  // Confirm delete item
  const handleConfirmDelete = async (item) => {
    try {
      await api.delete(`/inventory/${item.id}`);
      setDeleteModalItem(null);
      fetchInventory(activeSortNutrient);
      fetchAuxData();
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  // Handle nutrition bar click: autosort and transition to dashboard
  const handleSelectNutrientSort = (nutrient) => {
    setActiveSortNutrient(nutrient);
    setActiveTab("dashboard");
  };

  // Home button: exit kiosk mode to Raspberry Pi OS desktop
  const handleHomeExit = async () => {
    try {
      await api.post("/system/exit-kiosk");
    } catch (err) {
      console.warn("Backend exit-kiosk call:", err);
    }
    try {
      window.close();
    } catch (_) {}
  };

  return (
    <div className="min-h-screen bg-parchment text-gunmetal flex flex-col font-sans">
      {/* Persistent Kiosk Top Navbar */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onHome={handleHomeExit}
        scannerStatus={scannerStatus}
        storesStatus="not connected"
      />

      {/* Main Kiosk Content Screens */}
      <main className="flex-1">
        {activeTab === "dashboard" && (
          <DashboardPage
            items={items}
            activeSortNutrient={activeSortNutrient}
            onClearNutrientSort={() => setActiveSortNutrient(null)}
            onIncrement={handleIncrement}
            onDecrement={handleDecrement}
            onEdit={(item) => alert(`Editing '${item.product?.name}' (${item.product?.barcode})`)}
            onDelete={(item) => setDeleteModalItem(item)}
            onOpenScanModal={() => setIsScanModalOpen(true)}
          />
        )}

        {activeTab === "cart" && <CartPage />}

        {activeTab === "nutrition" && (
          <NutritionPage
            summary={nutritionSummary}
            onSelectNutrientSort={handleSelectNutrientSort}
          />
        )}
      </main>

      {/* Modals & Overlays */}
      <ScanFeedbackOverlay
        scanEvent={scanFeedbackEvent}
        onUndo={handleUndoScan}
        onClose={() => setScanFeedbackEvent(null)}
      />

      <DeleteConfirmModal
        item={deleteModalItem}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteModalItem(null)}
      />

      <ScanModal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        onScanBarcode={handleScanBarcode}
        sampleProducts={sampleProducts}
      />
    </div>
  );
}
