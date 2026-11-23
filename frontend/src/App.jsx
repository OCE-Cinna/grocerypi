/**
 * Main Application Component for GroceryPi.
 *
 * Manages the active screen tab (Dashboard, Cart, or Nutrition), loads kitchen
 * inventory and nutrition data from the FastAPI backend, listens for physical
 * barcode scans from the Raspberry Pi camera every second, and coordinates all
 * pop-up modals (Scan Feedback, Edit Item, Delete Confirmation, and Scan Modal).
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import Navbar from "./components/Navbar";
import DashboardPage from "./pages/DashboardPage";
import CartPage from "./pages/CartPage";
import NutritionPage from "./pages/NutritionPage";
import ScanFeedbackOverlay from "./components/ScanFeedbackOverlay";
import DeleteConfirmModal from "./components/DeleteConfirmModal";
import EditItemModal from "./components/EditItemModal";
import ScanModal from "./components/ScanModal";
import Modal from "./components/Modal";
import api from "./api/client";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [items, setItems] = useState([]);
  const [sampleProducts, setSampleProducts] = useState([]);
  const [nutritionSummary, setNutritionSummary] = useState(null);
  const [activeSortNutrient, setActiveSortNutrient] = useState(null);

  // Active pop-up modal states
  const [scanFeedbackEvent, setScanFeedbackEvent] = useState(null);
  const [deleteModalItem, setDeleteModalItem] = useState(null);
  const [editModalItem, setEditModalItem] = useState(null);
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [isSystemModalOpen, setIsSystemModalOpen] = useState(false);
  const [scannerInfo, setScannerInfo] = useState({
    state: "not_detected",
    label: "Not detected",
    hardwareDetected: false,
    canScan: false,
  });

  /**
   * Fetches the current list of kitchen inventory items from the backend,
   * optionally sorted by a specific nutrient (such as protein or sugar).
   */
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

  /**
   * Loads sample catalog products, the total pantry nutrition summary, and the
   * current status of the physical camera scanner.
   */
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
        const sData = scanRes.value.data || {};
        const host = window.location.hostname;
        const isLocalKioskHost = host === "localhost" || host === "127.0.0.1";
        const hwDetected = Boolean(sData.hardware_detected);

        if (hwDetected && isLocalKioskHost) {
          const state = sData.state || (sData.running ? "online" : "offline");
          setScannerInfo({
            state,
            label: sData.sensor_short_name || "Pi Camera v3",
            hardwareDetected: true,
            canScan: state === "online" || state === "lagging",
          });
        } else {
          setScannerInfo({
            state: "not_detected",
            label: isLocalKioskHost ? "Not detected" : "Not detected (Web)",
            hardwareDetected: false,
            canScan: false,
          });
        }
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

  /**
   * Checks the backend every second to see if the Raspberry Pi Camera Module v3
   * has scanned a new barcode in the background.
   */
  useEffect(() => {
    api
      .get("/scanner/latest-event")
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
            setScanFeedbackEvent(event);
            setIsScanModalOpen(false);
          }
        }
      } catch (err) {
        // Ignore temporary network hiccups during polling
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [fetchInventory, fetchAuxData, activeSortNutrient]);

  /**
   * Sends a manually typed or sample barcode scan to the backend.
   */
  const handleScanBarcode = async (barcode, confirmUnknown = false) => {
    try {
      const res = await api.post("/inventory/scan", {
        barcode: barcode.trim(),
        device_info: "Raspberry Pi Kiosk Interface",
        confirm_unknown: confirmUnknown,
      });

      if (res.data.scan_status === "SUCCESS") {
        setScanFeedbackEvent(res.data);
        fetchInventory(activeSortNutrient);
        fetchAuxData();
        if (confirmUnknown && res.data.inventory_item) {
          setScanFeedbackEvent(null);
          setEditModalItem({
            ...res.data.inventory_item,
            product: res.data.product,
          });
        }
      } else {
        setScanFeedbackEvent(res.data);
      }
    } catch (err) {
      console.error("Scan error:", err);
      alert("Failed to process scan event.");
    }
  };

  /**
   * Confirms adding an unrecognized barcode as a custom product and opens EditItemModal
   * so the user can give it a clear name and store tag.
   */
  const handleConfirmUnknownBarcode = async (barcode) => {
    await handleScanBarcode(barcode, true);
  };

  /**
   * Reverts a barcode scan when the user taps the 5-second 'Undo' button.
   */
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

  /**
   * Increases an item's stock count by +1 when tapping the plus button.
   */
  const handleIncrement = async (item) => {
    try {
      await api.patch(`/inventory/${item.id}`, { quantity: item.quantity + 1 });
      fetchInventory(activeSortNutrient);
      fetchAuxData();
    } catch (err) {
      console.error("Increment error:", err);
    }
  };

  /**
   * Decreases an item's stock count by -1, or opens the Delete confirmation modal
   * if the item is down to its last unit.
   */
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

  /**
   * Saves changes made inside EditItemModal (product name, package size,
   * preferred store badge, and custom restock interval days).
   */
  const handleSaveEdit = async (item, updates) => {
    try {
      const barcode = item.product?.barcode;
      if (barcode) {
        await api.patch(`/products/${encodeURIComponent(barcode)}`, {
          name: updates.name,
          package_size: updates.package_size,
          preferred_store: updates.preferred_store,
          is_frozen: updates.is_frozen,
        });
      }
      await api.patch(`/inventory/${item.id}`, {
        manual_interval_override: updates.manual_interval_override,
      });
      setEditModalItem(null);
      fetchInventory(activeSortNutrient);
      fetchAuxData();
    } catch (err) {
      console.error("Edit save error:", err);
      alert("Could not save changes to this item.");
    }
  };

  /**
   * Marks a stocked item as DEPLETED (0 units) and hides it from the active
   * Dashboard while preserving its learned restock interval for Cart Suggestions.
   * If the item is already depleted (viewed under 'Show Depleted'), permanently
   * deletes it from the database.
   */
  const handleConfirmDelete = async (item) => {
    try {
      const isAlreadyDepleted =
        item.status === "DEPLETED" || (item.quantity ?? 1) <= 0;
      if (isAlreadyDepleted) {
        await api.delete(`/inventory/${item.id}`);
      } else {
        await api.patch(`/inventory/${item.id}`, {
          quantity: 0,
          status: "DEPLETED",
        });
      }
      setDeleteModalItem(null);
      fetchInventory(activeSortNutrient);
      fetchAuxData();
    } catch (err) {
      console.error("Delete/deplete error:", err);
    }
  };

  /**
   * Sorts the Dashboard by a chosen nutrient when the user taps a bar or pie slice
   * on the Nutrition screen.
   */
  const handleSelectNutrientSort = (nutrient) => {
    setActiveSortNutrient(nutrient);
    setActiveTab("dashboard");
  };

  /**
   * Refreshes and restarts the application by pulling the latest GitHub updates,
   * resetting to the Dashboard, re-fetching database records, and reloading the page.
   */
  const handleRestartApp = async () => {
    setIsSystemModalOpen(false);
    setActiveTab("dashboard");
    setActiveSortNutrient(null);
    await Promise.allSettled([
      api.post("/system/git-pull"),
      fetchInventory(null),
      fetchAuxData(),
    ]);
    window.location.reload();
  };

  /**
   * Exits full-screen Chromium kiosk mode to return to the Raspberry Pi OS desktop.
   */
  const handleConfirmExitKiosk = async () => {
    setIsSystemModalOpen(false);
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
      {/* Fixed Top Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onHome={() => setIsSystemModalOpen(true)}
        scannerStatus={scannerInfo.label}
        scannerState={scannerInfo.state}
        storesStatus="Not connected"
        storesConnected={false}
      />

      {/* Main Kiosk Views */}
      <main className="flex-1">
        {activeTab === "dashboard" && (
          <DashboardPage
            items={items}
            activeSortNutrient={activeSortNutrient}
            onClearNutrientSort={() => setActiveSortNutrient(null)}
            onIncrement={handleIncrement}
            onDecrement={handleDecrement}
            onEdit={(item) => setEditModalItem(item)}
            onDelete={(item) => setDeleteModalItem(item)}
            onOpenScanModal={() => {
              if (scannerInfo.canScan) setIsScanModalOpen(true);
            }}
            canScan={scannerInfo.canScan}
            scannerStatus={scannerInfo.label}
          />
        )}

        {activeTab === "cart" && (
          <CartPage
            onCartSynced={() => {
              fetchInventory(activeSortNutrient);
              fetchAuxData();
            }}
          />
        )}

        {activeTab === "nutrition" && (
          <NutritionPage
            summary={nutritionSummary}
            onSelectNutrientSort={handleSelectNutrientSort}
          />
        )}
      </main>

      {/* Pop-Up Modals & Overlays */}
      <ScanFeedbackOverlay
        scanEvent={scanFeedbackEvent}
        onUndo={handleUndoScan}
        onConfirmUnknown={handleConfirmUnknownBarcode}
        onClose={() => setScanFeedbackEvent(null)}
      />

      <EditItemModal
        item={editModalItem}
        onSave={handleSaveEdit}
        onCancel={() => setEditModalItem(null)}
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

      {/* Logo Button System Menu Modal (Refresh/Restart vs. Close to Raspberry Pi OS Desktop) */}
      <Modal
        isOpen={isSystemModalOpen}
        onClose={() => setIsSystemModalOpen(false)}
        title="GroceryPi System Menu"
        subtitle="Would you like to refresh and restart the application, or close the kiosk to return to the Raspberry Pi OS desktop?"
      >
        <div className="space-y-3.5">
          <button
            type="button"
            onClick={handleRestartApp}
            className="w-full h-[74px] rounded-2xl bg-gunmetal hover:bg-gunmetal-dark text-white font-bold text-xl transition-all active:scale-98 flex items-center justify-center shadow-sm cursor-pointer"
          >
            Refresh / Restart Application
          </button>

          <button
            type="button"
            onClick={handleConfirmExitKiosk}
            className="w-full h-[74px] rounded-2xl bg-dustyRose hover:bg-dustyRose-dark text-gunmetal font-bold text-xl transition-all active:scale-98 flex items-center justify-center shadow-sm cursor-pointer"
          >
            Close to Desktop (Raspberry Pi OS)
          </button>

          <button
            type="button"
            onClick={() => setIsSystemModalOpen(false)}
            className="w-full h-[64px] rounded-2xl border-2 border-gunmetal bg-transparent hover:bg-gray-50 text-gunmetal font-bold text-lg transition-all active:scale-98 flex items-center justify-center cursor-pointer"
          >
            Cancel
          </button>
        </div>
      </Modal>
    </div>
  );
}
