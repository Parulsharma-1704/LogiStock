# LogiStock — Manual Testing Guide & Test Sheet

**Application:** LogiStock (Logistic Inventory Management System)  
**Environment:** Localhost (http://127.0.0.1:5000)  
**Database:** MongoDB (logistic_inventory)  
**Roles Tested:** \dmin\ and \staff\

---

## Pre-requisites & Test Setup

1. Start MongoDB service:
   \\\ash
   mongod --dbpath <data_dir>
   # or via Windows Services
   \\\
2. Seed baseline data:
   \\\powershell
   .\\venv\\Scripts\\python.exe seed.py
   .\\venv\\Scripts\\python.exe create_admin.py
   \\\
3. Verify test accounts:
   - **Admin:** \dmin\ / \Admin@123\
   - **Staff:** \staff\ / \Staff@123\ (created via seed or admin registration)
4. Launch application:
   \\\powershell
   .\\venv\\Scripts\\python.exe app.py
   \\\

---

## Test Cases Summary Matrix

| ID | Module | Feature Tested | Role | Expected Result | Status |
|---|---|---|---|---|---|
| TC-01 | Auth | Login with valid admin credentials | Guest | Redirects to Dashboard, admin badge visible | Pass |
| TC-02 | Auth | Login with wrong password | Guest | Shows error alert, stays on login page | Pass |
| TC-03 | Auth | Login with non-existent username | Guest | Shows error alert, stays on login page | Pass |
| TC-04 | Auth | Unauthenticated route protection | Guest | Redirects to \/login\ with warning flash | Pass |
| TC-05 | Auth | Logout | Admin/Staff | Clears session, redirects to \/login\ | Pass |
| TC-06 | Products | Add new product with valid data | Admin | Product added, success alert, in listing | Pass |
| TC-07 | Products | Add product with duplicate SKU | Admin | Rejected, error alert displayed | Pass |
| TC-08 | Products | Add product with negative quantity | Admin | Client/server validation blocks submission | Pass |
| TC-09 | Products | Add product with negative price | Admin | Client/server validation blocks submission | Pass |
| TC-10 | Products | Edit product details & price | Admin | Product updated, changes reflected | Pass |
| TC-11 | Products | Delete product | Admin | Removed from database, deleted flash | Pass |
| TC-12 | RBAC | Staff attempts GET /products/add | Staff | Returns HTTP 403 Forbidden | Pass |
| TC-13 | RBAC | Staff attempts POST /products/add | Staff | Returns HTTP 403 Forbidden | Pass |
| TC-14 | RBAC | Staff attempts product edit/delete | Staff | Returns HTTP 403 Forbidden | Pass |
| TC-15 | RBAC | Staff views product catalog & moves | Staff | Can browse products and perform stock ops | Pass |
| TC-16 | Stock Ops | Stock IN increases quantity | Staff/Admin | Product count increases, movement logged | Pass |
| TC-17 | Stock Ops | Stock OUT decreases quantity | Staff/Admin | Product count decreases, movement logged | Pass |
| TC-18 | Stock Ops | Stock OUT exceeding available stock | Staff/Admin | Operation blocked, error alert | Pass |
| TC-19 | Stock Ops | Stock OUT exact available stock (to 0)| Staff/Admin | Stock reaches 0, low-stock trigger | Pass |
| TC-20 | Dashboard | Low-stock badge & alert list | Staff/Admin | Items <= reorder level flagged red/amber | Pass |
| TC-21 | Search | Search by product name / SKU | Staff/Admin | Table filters accurately in real time | Pass |
| TC-22 | Security | CSRF token validation on POST | Guest/User | POST without valid CSRF rejected (400) | Pass |

---

## Detailed Step-by-Step Test Scenarios

### TC-01: Login with Valid Admin Credentials
1. Navigate to \http://127.0.0.1:5000/login\.
2. Enter Username: \dmin\, Password: \Admin@123\.
3. Click **Sign In**.
4. **Expected:** Redirects to \/\ (Dashboard). Welcome message appears. Admin navigation links (Add Product, Register User) are visible.

### TC-06 & TC-07: Product Creation & Duplicate SKU Check
1. Log in as \dmin\.
2. Click **+ Add Product** (\/products/add\).
3. Enter:
   - Name: \Heavy Duty Conveyor Belt\
   - SKU: \BELT-HD-100\
   - Category: \Machinery\
   - Quantity: \25\
   - Reorder Level: \5\
   - Price: \149.99\
   - Supplier: \Industrial Supply Co\
   - Location: \Warehouse A - Bay 4\
4. Submit the form.
5. **Expected:** Product appears in the product table. Total products & valuation on dashboard update.
6. Click **+ Add Product** again and submit the same SKU \BELT-HD-100\.
7. **Expected:** Error message *"SKU 'BELT-HD-100' already exists"* is displayed; duplicate record is not created.

### TC-12 & TC-13: Role Access Control (Staff Isolation)
1. Log in with credentials \staff\ / \Staff@123\.
2. Observe UI: **Add Product** and **Register User** buttons are hidden.
3. Manually type URL in browser: \http://127.0.0.1:5000/products/add\.
4. **Expected:** Browser receives HTTP 403 Forbidden. Staff cannot access administrative views.
5. Attempt POST to \/products/delete/<id>\ via curl/Postman with staff session cookie.
6. **Expected:** HTTP 403 Forbidden.

### TC-16, TC-17 & TC-18: Stock IN, Stock OUT & Boundary Tests
1. Find product \BELT-HD-100\ with initial quantity 25.
2. Click **Stock IN (+)**, enter quantity \10\, Reason/Notes: \Restock shipment #8812\.
3. Submit.
4. **Expected:** Quantity updates to \35\. Movement record logged with current user and timestamp.
5. Click **Stock OUT (-)**, enter quantity \5\, Reason: \Dispatched to client order\.
6. Submit.
7. **Expected:** Quantity updates to \30\. Movement logged as \OUT\.
8. Click **Stock OUT (-)**, enter quantity \50\ (greater than available 30).
9. Submit.
10. **Expected:** Flash message *"Insufficient stock. Cannot remove 50 units (current stock: 30)"*. Quantity remains 30. No faulty movement logged.
