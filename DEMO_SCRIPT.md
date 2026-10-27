# LogiStock — 5-Minute Live Demonstration Script

This script provides an engaging, confident presentation flow for showcasing LogiStock during reviews, project evaluations, or job interviews.

---

## Timing Breakdown

- **0:00 - 0:45 | Overview & Architecture:** Context, problem statement, technology stack.
- **0:45 - 1:45 | Authentication & Role-Based Access Control (RBAC):** Admin vs Staff experience.
- **1:45 - 2:45 | Inventory Management & Validation:** Adding products, duplicate SKU prevention, negative value safeguards.
- **2:45 - 3:45 | Stock Movements & Audit Logging:** Stock IN / OUT, insufficient stock prevention, movement audit log.
- **3:45 - 4:30 | Dashboard Analytics & Low Stock Alerts:** Real-time KPIs, visual cues, category aggregation.
- **4:30 - 5:00 | Automated Test Suite & Wrap-up:** Running pytest and closing remarks.

---

## Step-by-Step Flow

### Phase 1: The Pitch (0:00 - 0:45)
- **Speaker:** 
  > *\"Hello everyone. Today I'm presenting LogiStock, a secure, full-stack logistic inventory management system designed for warehouse operations.*  
  > *It is built with Python Flask and MongoDB using PyMongo, with a modern dark glassmorphism UI. We prioritized data integrity, role-based authorization, and real-time stock auditing.\"*
- **Action:** Open browser on http://127.0.0.1:5000/login.

---

### Phase 2: Role-Based Access Control (0:45 - 1:45)
- **Speaker:**
  > *\"Security is paramount in logistics. Let's start by logging in as a staff member with read and operational privileges.\"*
- **Action:** 
  1. Log in with staff / Staff@123.
  2. Show that **Add Product** and **Register User** buttons are absent from the navigation bar.
  3. Attempt to manually navigate to http://127.0.0.1:5000/products/add.
  4. Point out the immediate **HTTP 403 Forbidden** response:
     > *\"As you can see, permissions aren't just hidden on the frontend; routes are strictly guarded server-side using a custom @admin_required decorator.\"*
  5. Log out and sign in with dmin / Admin@123.
  6. Point out that the full admin toolbar is now visible.

---

### Phase 3: Inventory CRUD & Validation (1:45 - 2:45)
- **Speaker:**
  > *\"Now let's add an inventory item and inspect our validation safeguards.\"*
- **Action:**
  1. Click **+ Add Product**.
  2. Fill out:
     - Name: Precision Optical Sensor
     - SKU: SENS-OPT-01
     - Category: Electronics
     - Quantity: 50
     - Reorder Level: 10
     - Price: 89.50
  3. Submit and verify it appears in the catalog.
  4. Now click **+ Add Product** again and re-enter SENS-OPT-01:
     > *\"Notice what happens when I attempt to enter a duplicate SKU: MongoDB's unique index immediately triggers a graceful user notification rather than an unhandled 500 error.\"*
  5. Demonstrate negative quantity rejection: enter -10 in quantity; observe validation blocking it.

---

### Phase 4: Stock IN / OUT & Audit Trail (2:45 - 3:45)
- **Speaker:**
  > *\"In a busy warehouse, goods constantly arrive and leave. Let's record inventory movements.\"*
- **Action:**
  1. Find Precision Optical Sensor (quantity 50).
  2. Click **Stock IN (+)**, add 20 units with note \"Received batch PO-401\".
  3. Quantity immediately increments to 70.
  4. Click **Stock OUT (-)**, attempt to remove 100 units:
     > *\"The system prevents stockouts by validating requested quantities against existing stock before writing changes.\"*
  5. Show the flash alert: *\"Insufficient stock\"*.
  6. Perform a valid Stock OUT of 15 units.
  7. Navigate to /movements:
     > *\"Every transaction is permanently audited with the user identity, operation type, quantity delta, and UTC timestamp.\"*

---

### Phase 5: Dashboard Analytics & Low Stock Triggers (3:45 - 4:30)
- **Speaker:**
  > *\"Warehouse managers need immediate visibility into shortages and asset value.\"*
- **Action:**
  1. Navigate to the **Dashboard** (/).
  2. Point out:
     - Real-time inventory valuation ($ value aggregated using MongoDB pipeline).
     - Stock count by category breakdown.
     - **Low Stock Alert Section:** Point to items highlighted where current quantity is below or equal to the reorder threshold.

---

### Phase 6: Code Quality & Automated Tests (4:30 - 5:00)
- **Speaker:**
  > *\"Finally, we built a comprehensive automated test suite with pytest. All tests execute against an isolated test database, ensuring zero contamination of production data.\"*
- **Action:**
  1. Switch to terminal:
     `powershell
     .\venv\Scripts\python.exe -m pytest tests/ -v
     `
  2. Let the 22 passing tests scroll on screen:
     > *\"All 22 unit and integration tests pass, covering authentication, CRUD, edge cases, RBAC, and stock movements. Thank you, and I welcome any questions!\"*
