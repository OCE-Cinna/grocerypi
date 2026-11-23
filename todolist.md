# GroceryPi — Sprint 3 & Sprint 4 Implementation TODO List

> [!IMPORTANT]
> Aligned with **Project Plan v4 (Section 2.3/2.4)**, **C4 Architecture Model (Level 3)**, **Sprint 2 Action Plan**, and **Expert Coach Feedback** from **Patrick** (Software Level 2, SOLID & folder architecture) and **Pieter** (UI/UX Level 1, Norman Nielsen heuristics & visual alignment).

---

## Phase 3 (Sprint 3): Frontend UI, Backend Refactoring & Basic Integration
**Timeline:** 9 Nov 2026 – 27 Nov 2026 (24 hrs)

### Epic 3.1 — Backend Folder Restructuring & SOLID Clean Architecture (Coach Patrick Feedback)

#### User Story 3.1.1 — Modular Inventory Service & Repository Layer
> **As a** full-stack developer demonstrating HBO-ICT Software Level 2,  
> **I want to** move all inventory ingestion and stock management logic out of `backend/app/main.py` and `backend/app/routers/inventory.py` into a dedicated `backend/app/services/inventory/inventory.py` module backed by repositories,  
> **So that** hardware barcode scans and REST API scans share one Single Responsibility (`SRP`) service without duplicated code.

- [x] **Step 1 (Fri 13 Nov 2026, 09:00–10:30):** Create `backend/app/services/inventory/__init__.py` and `backend/app/services/inventory/inventory.py` containing an `InventoryService` class.
- [x] **Step 2 (Fri 13 Nov 2026, 10:30–12:30):** Consolidate the duplicate barcode scan ingestion logic currently in `backend/app/main.py` (`handle_hardware_scan`) and `backend/app/routers/inventory.py` (`ingest_barcode_scan`) into `InventoryService.ingest_scan(barcode, device_info)`.
- [x] **Step 3 (Fri 13 Nov 2026, 13:15–14:45):** Create `backend/app/db/repositories/inventory_repository.py` and `product_repository.py` to encapsulate SQLAlchemy queries (`get_by_barcode`, `upsert_stock_on_scan`, `log_scan`, `list_filtered`).
- [x] **Step 4 (Fri 13 Nov 2026, 14:45–15:30):** Extract the 80-line nutrition aggregation calculation from `backend/app/routers/inventory.py` (`get_nutrition_summary`) into `backend/app/services/nutrition/nutrition.py` (`NutritionService.get_pantry_summary()`).

#### User Story 3.1.2 — Slim `main.py` & Dedicated Scanner/System Routers
> **As a** backend developer,  
> **I want** `backend/app/main.py` to only handle FastAPI initialization, middleware, lifespan hooks, and router registration,  
> **So that** route controllers are cleanly separated by domain.

- [x] **Step 1 (Fri 13 Nov 2026, 15:30–16:00):** Move `/scanner/status`, `/scanner/preview`, `/scanner/frame`, `/scanner/latest-event`, `/scanner/start`, and `/scanner/stop` out of `backend/app/main.py` into `backend/app/routers/scanner.py`.
- [x] **Step 2 (Fri 13 Nov 2026, 16:00–16:20):** Move `/system/exit-kiosk` out of `backend/app/main.py` into `backend/app/routers/system.py`.
- [x] **Step 3 (Fri 13 Nov 2026, 16:20–17:00):** Move `backend/app/services/scanner.py` into `backend/app/services/scanner/scanner.py` and `backend/app/services/prediction.py` into `backend/app/services/prediction/prediction.py`.
- [x] **Step 4 (Wed 18 Nov 2026, 10:00–12:15):** Audit and clean up legacy Phase 1 list boilerplate (`routers/lists.py`, `routers/items.py`) while **retaining and organizing** `backend/app/auth.py` and `backend/app/routers/auth.py` (`User` model with `bcrypt` hashed passwords) for the Sprint 4 mobile web prototype, and add 5 Phase 3 unit tests in `test_phase3_architecture.py` (15/15 passing).
- [x] **Step 5 (Wed 18 Nov 2026, 12:15–14:00):** Untrack `backend/app/db/ah_product_cache.json` and add it to `.gitignore` for household invoice privacy while updating `seed_data.py` to seed local development databases cleanly.

---

### Epic 3.2 — Real-Time Frontend–Backend Kiosk Integration & UX Alignment (Coach Pieter Feedback)

#### User Story 3.2.1 — Real-Time Hardware Scan & Undo Loop
> **As a** household user in the kitchen (Partner P.),  
> **I want** physical barcode scans on the Pi Camera v3 to immediately update the 7-inch kiosk display with a 5-second Undo overlay,  
> **So that** I can check items IN hands-free and instantly revert accidental double-scans without manual typing.

- [x] **Step 1 (Wed 11 Nov 2026, 11:30–12:30):** Poll `/scanner/latest-event` from `frontend/src/App.jsx` and trigger `ScanFeedbackOverlay.jsx` with 5-second auto-dismiss timer *(Implemented on `test-phase2-ui`)*.
- [x] **Step 2 (Wed 11 Nov 2026, 12:30–13:30):** Add camera preview toggle (`Preview Active` / `Preview Off`) and standby view in `ScanModal.jsx` *(Implemented on `test-phase2-ui`)*.
- [x] **Step 3 (Mon 23 Nov 2026, 13:00–14:30 · Camera FPS vs. Decode Throttling):** Update `backend/app/services/scanner/scanner.py` so the camera capture and live preview run at a comfortable, smooth `12 FPS` for the user, while barcode scanning/decoding (`_async_decode`) only triggers every `0.75` seconds (`0.5`–`1.0s`) to avoid slowing down the Raspberry Pi app.
- [x] **Step 4 (Mon 23 Nov 2026, 15:45–16:45 · Motion-Blur Barcode Validation & Redo/Confirm Prompt):**
  - Restrict `pyzbar` to retail grocery barcode formats (`EAN-13`, `EAN-8`, `UPC-A`, `UPC-E`) and validate the **GS1 Modulo-10 Check Digit** so motion-blurred or misread numbers are rejected before reaching the database.
  - Tune Picamera2 camera controls (short exposure mode & higher sharpness) and add a frame sharpness check to reduce motion-blur misreads without needing an external USB barcode scanner (keep compact USB scanner as a low-cost future hardware option in backlog).
  - Stop silently inserting unrecognized barcodes into the database; instead, show an **Unrecognized Barcode** prompt asking the user to **Redo Scan** or **Confirm & Add Item**.
- [x] **Step 5 (Mon 23 Nov 2026, 16:45–17:15 · Dutch / English Only Product Lookup on Open Food Facts):**
  - Update `get_product_from_openfoodfacts()` in `backend/app/services/ah_client.py` to query `nl.openfoodfacts.org` with `Accept-Language: nl,en` and strictly prioritize `product_name_nl`, `product_name_en`, `generic_name_nl`, and `generic_name_en` so international brands (like Calvé or cereal bars) never pull German, Spanish, or French product titles.

#### User Story 3.2.2 — Functional Item Edit Modal (Replacing Placeholder Alert)
> **As a** household user shopping across Albert Heijn, Jumbo, and Lidl,  
> **I want to** tap the Edit button on any inventory card to change its preferred store badge (`[AH]`, `[Jumbo]`, `[Lidl]`), product name/package size, or custom restock interval days,  
> **So that** non-AH items or dual-store products are routed to the right shopping cart queue.

- [x] **Step 1 (Fri 20 Nov 2026, 13:15–15:15):** Build `frontend/src/components/EditItemModal.jsx` with large touch selectors for Store (`AH`, `Jumbo`, `Lidl`, `Other`), Product Name, Package Size, and Restock Interval override (in days).
- [x] **Step 2 (Fri 20 Nov 2026, 15:15–16:15):** Replace the placeholder `onEdit={(item) => alert(...)}` in `frontend/src/App.jsx` with `EditItemModal` wired to `PATCH /inventory/{item_id}` and `PATCH /products/{barcode}`.
- [x] **Step 3 (Fri 20 Nov 2026, 16:15–17:00):** Ensure `PATCH /inventory/{item_id}` in `backend/app/routers/inventory.py` saves `manual_interval_override` and `is_dual_store`.

#### User Story 3.2.3 — Visual Alignment & Norman Nielsen UX Compliance (Coach Pieter Feedback)
> **As a** kiosk user viewing the 7-inch display at eye level,  
> **I want** consistent vertical and horizontal alignment across all cards, badges, and buttons,  
> **So that** the screen is effortless to scan visually under bright kitchen lighting.

- [x] **Step 1 (Fri 20 Nov 2026, 09:00–12:30):** Implement a 5-column vertical grid alignment across `Navbar.jsx`, `DashboardPage.jsx`, and `GroceryCard.jsx` (left-aligning store tag + item name, right-aligning category/diet/Nutri-Score badges, and aligning action buttons under the `Scan New Item` column).
- [x] **Step 1b (Mon 23 Nov 2026, 14:30–15:45):** Use `Modal.jsx` when clicking the `GroceryPi` logo button to open a System Menu popup asking whether to **Refresh / Restart Application** (with automatic `POST /system/git-pull`) or **Close to Desktop (Raspberry Pi OS)**, and fix the Raspberry Pi `~/.config/labwc/autostart` + `5555` GNOME Keyring lock over SSH.
- [ ] **Step 2 (Planned Fri 27 Nov 2026):** Update Section 6 of the *UI Design Decisions & Wireframe Blueprint* document to explicitly map every kiosk rule to **Jakob Nielsen's 10 Usability Heuristics**.
- [ ] **Step 3 (Planned Fri 27 Nov 2026):** Add a formal conclusion to the UI Design Decisions document justifying the final UI using UX theory, component specifications, and user test results.

#### User Story 3.2.4 — Live Navbar Hardware Scanner Status Dot & Non-Kiosk Scanning Lock
> **As a** user viewing GroceryPi on either the physical Raspberry Pi kiosk or a web/mobile browser,  
> **I want** the top navbar `Scanner` indicator to detect the Raspberry Pi Camera Module v3, show its name with a colored status dot (green = online, yellow = lagging, red/gray = offline or not detected), and disallow barcode scanning when opened on a regular web browser or mobile phone,  
> **So that** I always know the real hardware state and cannot trigger invalid scans outside the physical kitchen kiosk.

- [x] **Step 1:** Update `/scanner/status` and `backend/app/services/scanner/scanner.py` to detect real Raspberry Pi camera hardware vs. non-Pi web/mobile environments and report `hardware_detected`, `sensor_short_name` (e.g., `"Pi Camera v3"`), and health `state` (`"online"`, `"lagging"`, `"offline"`, or `"not_detected"` based on frame age).
- [x] **Step 2:** Update `Navbar.jsx` to render a status dot (green = online, amber = lagging, red = offline/not detected) alongside the scanner label (e.g., `Scanner · ● Pi Camera v3` on kiosk, or `Scanner · ● Not detected` on browser/mobile) and a status dot for `Stores`.
- [x] **Step 3:** Disallow barcode scanning (`Scan New Item`) when no physical scanner hardware is detected (web browser / mobile mode), locking scan actions cleanly.

---

### Epic 3.3 — User Testing & Portfolio Validation (Sprint 3 Milestone)

#### User Story 3.3.1 — Multi-User Kiosk Flow & UX Testing
> **As a** researcher validating User Interaction (Level 1) and Software (Level 2),  
> **I want to** test the physical GroceryPi kiosk flow with Partner P., peers (Koen, Evy, fellow students), and teachers using a structured 2-minute evaluation form,  
> **So that** I can identify friction points and prioritize Sprint 4 & 5 improvements with real evidence.

- [x] **Step 1:** Conduct 2-minute hands-on user test sessions using the standardized User Testing Form *(Session #1 completed on 23 Nov 2026 with Primary Stakeholder Peter on 7-inch Raspberry Pi kiosk; peer/coach sessions scheduled for 24 Nov Demo Market)*.
- [x] **Step 2:** Summarize quantitative ratings and qualitative quotes in the Sprint 3 Devlog and Feedback Log.
- [ ] **Step 3:** Book validation check-ins with **Patrick** (review refactored backend folders) and **Pieter** (review Norman Nielsen alignment & user test findings) and upload snapshot to Portflow.

---

### Epic 3.4 — Automated "Items IN" Depletion, Midnight Replenishment & Cart Sync Lifecycle

#### User Story 3.4.1 — Same-Day Multi-Scan Batching vs. New-Day (Midnight 00:00) Replenishment Reset
> **As a** household user who scans multiple units of the same product on shopping day and scans new units on later days without ever scanning items OUT,  
> **I want** multiple scans on the same calendar day (before `00:00` midnight) to increment the quantity (`1 → 2 → 3`), while the first scan on a new calendar day (after `00:00` midnight) automatically treats the previous batch as used, updates the learned restock interval in the database, and resets the stock count to `1` for the new batch,  
> **So that** stock counts stay accurate without manual subtraction.

- [x] **Step 1:** Update `InventoryRepository.upsert_stock_on_scan()` in `backend/app/db/repositories/inventory_repository.py` to compare the local calendar date of `last_restocked_at` against the current scan's calendar date (`00:00` midnight boundary).
- [x] **Step 2:** When scanning on the **same calendar day** while `IN_STOCK`, increment `quantity += 1`. When scanning on a **new calendar day** (or when `DEPLETED`), recalculate the rolling `restock_interval_days` from the elapsed days of the previous batch and reset `quantity = 1` (`IN_STOCK`).

#### User Story 3.4.2 — Automatic Dashboard Depletion (Predicted Interval or 30-Day Cap)
> **As a** household user who wants the Dashboard to only show what is currently available in the kitchen,  
> **I want** items that have reached their predicted consumption interval (e.g., 7 days for milk, 28 days for soap) or a maximum 30-day shelf cap to automatically transition to `DEPLETED` (`quantity = 0`), hide visually from the main Dashboard, and appear in Cart Suggestions while keeping their learned interval in the database,  
> **So that** finished or expired items leave the active Dashboard automatically.

- [x] **Step 1:** Add `InventoryRepository.apply_auto_depletion(db, now_utc)` to automatically transition `IN_STOCK` items to `InventoryStatus.DEPLETED` (`quantity = 0`) once `days_elapsed >= min(effective_interval_days, 30.0)`, preserving `restock_interval_days` in `grocerypi.db`.
- [x] **Step 2:** Hide `DEPLETED` (`0` unit) items from the default Dashboard view in `frontend/src/pages/DashboardPage.jsx`, and add a clean filter toggle button (`Show Depleted / Synced`) so users can optionally inspect depleted items and their learned intervals.

#### User Story 3.4.3 — Cart Sync Visual Removal & Unpurchased Item Retention
> **As a** shopper syncing recommended items to my supermarket cart,  
> **I want** items synced to the cart to be immediately removed visually from the active kitchen Dashboard while remaining in Cart Suggestions (marked as synced/waiting for scan-in) until I physically scan them IN after shopping,  
> **So that** if I forget or skip buying an item at the store, its learned interval is kept in the database and it stays on my shopping list for the next trip.

- [x] **Step 1:** Add `POST /inventory/cart/sync/{store}` in `backend/app/routers/inventory.py` and `InventoryService.sync_store_cart(db, store)` to mark all items in the selected store queue (`AH`, `Jumbo`, `Lidl`) as `InventoryStatus.DEPLETED` (`quantity = 0`), removing them visually from the active Dashboard while retaining their database interval and keeping them in Cart Suggestions until scanned IN again.
- [x] **Step 2:** Wire `handleSyncCart` in `frontend/src/pages/CartPage.jsx` to call `POST /inventory/cart/sync/{activeQueueId}`, refresh the Dashboard state in `App.jsx`, and display a `'Synced · waiting to scan in'` badge on synced items in the Cart view.

#### User Story 3.4.4 — 7-Inch Card Tag Decluttering & Tap-to-Expand Details Drawer
> **As a** kiosk user viewing the 7-inch touchscreen (`720×1280`) where action buttons occupy 2/5 of each card's width,  
> **I want** compact single-letter Nutri-Score badges (`[A]`–`[E]`), secondary category/diet tags moved to the 2nd subtitle row (and hidden when `'Depleted · In Cart'` is displayed), plus the ability to tap a card's left info area to expand full product and nutrition details,  
> **So that** product titles are never truncated or crowded out by multiple badges.

- [x] **Step 1:** Update `frontend/src/components/GroceryCard.jsx` to use an adaptive minimalist-to-tags format: when collapsed, display only the clean Product Name on the top line and render Store, Category, Frozen, Diet (`Vegan` / `Vegetarian`), and Nutri-Score as minimalist `·`-separated subtitle text (hiding Frozen/Diet/Nutri-Score when `'Depleted · In Cart'` is active); when tapped to expand, display all metadata as visual pill/tag badges (`[Store: AH]`, `[Food]`, `[Frozen · Freezer]`, `[Vegan]`, `[Nutri-Score A]`, `[EAN]`) plus per-100g macros.
- [x] **Step 2:** Update `DeleteConfirmModal.jsx` and `handleConfirmDelete` in `frontend/src/App.jsx` so deleting a stocked item marks it as `DEPLETED` (`quantity = 0`) and hides it from the active Dashboard while preserving its learned `restock_interval_days` for Cart Suggestions (and only permanently deletes from the database if confirmed on an already-depleted item).

#### User Story 3.4.5 — Frozen & Non-Food 30-Day Cap Exemption, AH/OFF Freezer Auto-Detection & Non-Blocking Depletion Banner
> **As a** household user storing freezer items (frozen vegetables, fries, fruit) and non-food products (`Household`, `Hygiene`, `Pet`) that last longer than 30 days,  
> **I want** GroceryPi to automatically detect frozen products from the Albert Heijn (`mainCategory: "Diepvries"`) and Open Food Facts (`frozen-foods`) APIs, allow toggling `Frozen / Freezer` in `EditItemModal`, exempt frozen and non-food items from the 30-day shelf cap, and show a non-blocking top banner on the Dashboard when items reach 75% / 100% of their cycle,  
> **So that** long-lasting freezer and household items are never prematurely auto-depleted at 30 days and can be reviewed without blocking startup modals.

- [x] **Step 1:** Add `is_frozen` (`Boolean`) to `ProductCatalog` in `backend/app/models.py`, `backend/app/schemas.py`, and `backend/app/database.py` (with automatic SQLite `ALTER TABLE` migration), and implement `detect_is_frozen()` in `backend/app/services/ah_client.py` to auto-detect freezer items from AH (`"Diepvries"`) and Open Food Facts (`"en:frozen-foods"`, `"nl:diepvries"`).
- [x] **Step 2:** Add a **`Storage Type: Pantry / Fridge vs. Frozen (Freezer)`** toggle in `frontend/src/components/EditItemModal.jsx` and wire it through `PATCH /products/{barcode}` in `frontend/src/App.jsx`.
- [x] **Step 3:** Update `InventoryRepository.apply_auto_depletion()` in `backend/app/db/repositories/inventory_repository.py` so the 30-day shelf cap applies only to non-frozen `Food` items, while `Frozen` and non-food (`Household`, `Hygiene`, `Pet`) items use their full restock interval (up to 180 days).
- [x] **Step 4:** Add a non-blocking top review banner on `frontend/src/pages/DashboardPage.jsx` showing how many items reached `100%` (depleted / in cart) or `75%+` (running low) of their restock cycle with quick **Review Items** and **Dismiss** buttons.

---

## Phase 4 (Sprint 4): Supermarket API, Prediction Engine & Cart Automation
**Timeline:** 30 Nov 2026 – 18 Dec 2026 (24 hrs) | **Demo Milestone:** Dec 9, 2026

### Epic 4.1 — SOLID Supermarket Gateway (`IStoreGateway`) & Multi-Store Routing

#### User Story 4.1.1 — Polymorphic `IStoreGateway` Interface (SOLID OCP / LSP / DIP)
> **As a** software architect,  
> **I want** external supermarket and product APIs to implement an abstract `IStoreGateway` interface (`backend/app/clients/store_gateway.py`),  
> **So that** Albert Heijn, Jumbo, Lidl, and Open Food Facts can be queried or swapped without changing `InventoryService`.

- [x] **Step 1:** Define `IStoreGateway(ABC)` in `backend/app/clients/store_gateway.py` with abstract methods `lookup_by_barcode(barcode: str)`, `search_product(query: str)`, and `sync_cart(items: List[Dict[str, Any]])`.
- [x] **Step 2:** Create `backend/app/clients/ah_gateway.py` (`AHStoreGateway(IStoreGateway)` and `JumboStoreGateway(IStoreGateway)`) and `backend/app/clients/off_client.py` (`OpenFoodFactsClient(IStoreGateway)`).
- [x] **Step 3:** Implement store tag auto-detection in `OpenFoodFactsClient` (`infer_preferred_store_from_off`, detecting `"Jumbo"`, `"Lidl"`, and private-label brands like `"Milbona"`, `"Crownfield"`, `"W5"`, `"1 de Beste"` in OFF `brands` / `stores_tags` so non-AH barcodes automatically get tagged with `PreferredStore.JUMBO` or `PreferredStore.LIDL`).

---

### Epic 4.2 — Empirical "Items IN" Depletion Prediction Engine

#### User Story 4.2.1 — Dynamic Rolling Consumption Interval Calculation
> **As a** household stakeholder who never logs "Items OUT",  
> **I want** the backend to automatically recalculate an item's average consumption interval (`Interval = Days / Units`) every time I scan it IN,  
> **So that** my restock predictions adapt to how fast we actually consume milk, eggs, or coffee.

- [x] **Step 1:** Enhance `InventoryService.ingest_scan` and `PredictionEngine` (`backend/app/services/prediction/prediction.py`) to compute the elapsed days between historical `ScanLog` / `PurchaseOrder` timestamps for that `product_id`.
- [x] **Step 2:** Update `InventoryItem.restock_interval_days` using a rolling average of scan-in intervals, and compute `predicted_depletion_at = last_restocked_at + timedelta(days=effective_interval * quantity)`.
- [x] **Step 3:** Automatically transition `InventoryItem.status` from `IN_STOCK` → `PREDICTED_LOW` (`interval_ratio >= 0.75`) → `DEPLETED` (`interval_ratio >= 1.0`), surfacing urgency badges on both Dashboard and Cart views.

---

### Epic 4.3 — Automated Cart Synchronization & Error Recovery

#### User Story 4.3.1 — End-to-End Cart Sync Endpoint & Frontend Wiring
> **As a** household user on the Shopping Cart screen,  
> **I want** tapping *"Sync Recommended Items to Supermarket Cart"* to call a real backend sync endpoint (`POST /cart/sync/{store}`) with clear error/fallback handling,  
> **So that** recommended items are pushed to our supermarket list and marked as synced.

- [x] **Step 1:** Create `backend/app/routers/cart.py` with `GET /cart/suggestions`, `GET /cart/stores/status`, `POST /cart/stores/connect/{store}`, and `POST /cart/sync/{store}` (supporting `AH`, `Jumbo`, and `Lidl` queues, plus local list export/fallback when unauthenticated).
- [x] **Step 2:** Research and implement the safest direct cart/list sync method for **Albert Heijn** and **Jumbo** (using direct web/mobile app shopping list deep-links `https://www.ah.nl/mijnlijst`, `appie://shoppinglist`, `https://www.jumbo.com/lijstjes`, and `jumbo://shoppinglist` so user accounts are never banned for botting).
- [x] **Step 3:** Replace the mock `setTimeout` in `frontend/src/pages/CartPage.jsx` (`handleSyncCart`) with a real `api.post(\`/cart/sync/\${activeQueueId}\`)` call, displaying synced item counts, timestamp, direct web list link, and error fallback states.
- [x] **Step 4:** Update `storesStatus` in `frontend/src/App.jsx` and `Navbar.jsx` to display which real supermarket account/application is actively connected for cart syncing (e.g., `Stores · ● AH Connected`, `Stores · ● AH & Jumbo`, or `Stores · ● Not connected` when only using anonymous catalog lookup).

#### User Story 4.3.2 — Automated Unit & Integration Test Suite
> **As a** developer ensuring data consistency and risk mitigation,  
> **I want** automated `pytest` tests covering the refactored `InventoryService`, `PredictionEngine`, `NutritionService`, and `IStoreGateway` fallback chain,  
> **So that** regressions are caught before deploying to the Raspberry Pi kiosk.

- [x] **Step 1:** Expand `backend/tests/test_phase3_architecture.py` and `backend/tests/test_phase2_inventory.py` to test rolling interval updates, `AHStoreGateway` → `OpenFoodFactsClient` → placeholder fallback chain, store routing, `/cart/sync/{store}`, and `PATCH /inventory/{id}`.

---

### Epic 4.4 — Online Mobile Web Prototype with Hashed Password Auth & DB/Cart Sync *(Lower Backlog Priority)*

#### User Story 4.4.1 — Hashed-Password Gate for Remote Mobile Access
> **As a** household user away from the kitchen (e.g., shopping inside Albert Heijn, Jumbo, or Lidl),  
> **I want to** access a mobile-responsive web version of GroceryPi online that requires a hashed password to unlock,  
> **So that** I can securely view and interact with our household inventory and shopping cart without exposing our database publicly.

- [x] **Step 1:** Refactor and wire the existing `bcrypt` password hashing and JWT bearer token authentication in `backend/app/auth.py` (`hash_password`, `verify_password`, `get_current_user`) and `backend/app/routers/auth.py` into a clean `backend/app/services/auth/` service (`AuthService`).
- [x] **Step 2:** Configure conditional auth protection on API and frontend routes: allow local Raspberry Pi kiosk traffic (`localhost` / `127.0.0.1`) to stay zero-friction hands-free, while requiring valid JWT / hashed-password login when accessed remotely via mobile browser (`!isLocalKiosk` or `?mobile=1`).
- [x] **Step 3:** Style `frontend/src/pages/LoginPage.jsx` and `frontend/src/context/AuthContext.jsx` to match the GroceryPi kitchen color palette (Gunmetal `#383D3B`, Parchment `#F7F4F2`, Lime Cream `#C3E48B`) and gate mobile routes behind authentication.

#### User Story 4.4.2 — Mobile Web Prototype UI & Live Database / Grocery App Sync
> **As a** mobile shopper in the supermarket aisle,  
> **I want** a responsive mobile web view connected to the GroceryPi database and grocery app sync,  
> **So that** I can check off replenished items, view current pantry stock on my phone, and trigger or verify supermarket cart synchronization on the go.

- [x] **Step 1:** Optimize mobile viewport layouts (`< 640px`) across `Navbar.jsx`, `DashboardPage.jsx`, and `CartPage.jsx` (compact responsive mobile navigation and status badges, thumb-friendly store queue tabs, and locked scanning outside the physical kiosk).
- [x] **Step 2:** Add an in-store mobile checklist / restock interaction in `CartPage.jsx` (`POST /cart/restock/{item_id}`, `"Bought (+1)"` button) allowing mobile shoppers to mark suggested items as bought/restocked in real time.
- [x] **Step 3:** Test end-to-end hashed-password login + live database and cart restock sync (`test_phase3_architecture.py`).

---

### Epic 4.5 — Primary Stakeholder (Peter) User Test Action Items (23 Nov 2026 Kiosk Session)

#### User Story 4.5.1 — Pivot from "Live Stock Inventory" to "Check-In Batch Staging & Purchase History Log" (#1 Make-or-Break Priority)
> **As a** household user who never wants to manage live pantry stock counts,  
> **I want** the main screen to act as a **"Current Check-In Batch"** (staging items just scanned in after a shopping trip) that clears upon tapping **"Finish Check-In"** (or automatically at midnight / configurable time) into a searchable **"Purchase History"** log (`"You submitted X items on [Date · Time]"`),  
> **So that** the app functions purely as a low-friction purchase tracker and restock predictor rather than an inventory manager.

- [ ] **Step 1:** Reframe the Dashboard into a **Check-In Batch Staging List** with a prominent **"Finish & Submit Batch"** button (replacing `"Your kitchen, stocked."` hero copy) and move the Search bar into a dedicated **Purchase History** tab/panel showing timestamped past check-in batches.
- [ ] **Step 2:** Dynamically adapt or hide the secondary filter bar based on the active Category (e.g., show `DIET: All / Vegetarian / Vegan` only when `Food` is selected, and align filter buttons cleanly without the offsetting `DIET:` label).

#### User Story 4.5.2 — Scan Overlay Timer Customization (10–30s), Rapid-Scan Animation Reset & Settings Menu with GitHub Update Badge
> **As a** user scanning multiple groceries in a row on the 7-inch kiosk,  
> **I want** the Scan Feedback Overlay to stay visible for a configurable `10–30 seconds`, restart its countdown animation cleanly when scanning back-to-back items rapidly, and have an explicit **Settings / Menu** button with an hourly GitHub **`Update Available (!)`** indicator,  
> **So that** I always have enough time to read scan details and can see when a new GitHub update is ready to pull.

- [ ] **Step 1:** Key the countdown bar animation in `ScanFeedbackOverlay.jsx` to `scanEvent.scan_id` (so rapid consecutive scans restart the timer from 100%) and increase the default auto-dismiss duration to `12–15s` (configurable between `10s` and `30s` in Settings).
- [ ] **Step 2:** Add an explicit **Menu / Settings** button in `Navbar.jsx` and a background check (`GET /system/update-status` every hour) that displays an **`! Update Available`** badge when new commits exist on `origin`.

#### User Story 4.5.3 — Edit Modal Interval Restoration, Quick Presets, Unit Selector & On-Screen Touch Keyboard
> **As a** kiosk user editing an item on the 7-inch touchscreen,  
> **I want** toggling `Frozen (45d)` back to `Pantry / Fridge` to restore the original pantry interval, quick interval preset buttons (`3d`, `7d`, `14d`, `30d`, `45d`), a constrained package unit selector (`g`, `kg`, `ml`, `L`, `pack`, `unit`), and an automatic on-screen touch keyboard when tapping text fields,  
> **So that** I never have to tap `-` 40 times or need a physical keyboard on Raspberry Pi OS.

- [ ] **Step 1:** Save the previous non-frozen interval in `EditItemModal.jsx` so switching `Frozen → Pantry / Fridge` restores it immediately, add quick-tap preset pills (`3d`, `5d`, `7d`, `14d`, `30d`, `45d`), and split Package Size into a numeric input + fixed unit dropdown.
- [ ] **Step 2:** Integrate an on-screen virtual touch keyboard (or Raspberry Pi OS `wvkbd` / `squeekboard` / React touch keyboard modal) when focusing Product Name or Package Size inputs, and round all expanded card nutrition macros in `GroceryCard.jsx` to at most 2 decimal places (`Number(val.toFixed(2))`).

#### User Story 4.5.4 — Inline Expandable Macro Item Lists in Nutrition View
> **As a** user exploring nutritional breakdowns on the Nutrition screen,  
> **I want** clear visual affordance that macro bars are interactive, and tapping a macro bar to unfold a condensed list of matching items **inline inside the Nutrition screen** (rather than jumping back to the Dashboard),  
> **So that** Dashboard sorting and Nutrition exploration stay clean and non-redundant.

- [ ] **Step 1:** Add an explicit `"Tap any nutrient bar to view matching items"` hint in `NutritionPage.jsx` and render an inline, condensed accordion list of items sorted by the tapped macro directly beneath the chart.
