# LogiStock — Technical Viva & Evaluation Guide

This document contains key conceptual and technical questions, architectural rationales, and model answers to prepare for project evaluations, academic vivas, and technical interviews.

---

## 1. System Architecture & Design Choices

### Q1: Why choose Flask over heavier frameworks like Django?
**Answer:**  
Flask is a microframework that provides flexibility and minimalist overhead. For LogiStock, Flask gave us precise control over middleware, authentication with Flask-Login, and seamless direct integration with PyMongo without the heavy constraints of an ORM like Django ORM or SQLAlchemy, which are traditionally built for relational databases.

### Q2: Why MongoDB instead of PostgreSQL or MySQL?
**Answer:**  
1. **Document Flexibility:** Inventory items often evolve with dynamic attributes (such as supplier specifications, warehouse locations, and custom metadata) that fit naturally into BSON documents without rigid migrations.
2. **Atomic Operations:** MongoDB natively supports atomic in-place updates (such as $inc for inventory increments/decrements) at the document level without requiring complex locking or transaction overhead for single-document stock adjustments.
3. **Rich Aggregation Framework:** Multi-stage aggregation pipelines ($group, $sum, $sort) make computing total valuation, units per category, and KPI analytics extremely fast.

---

## 2. Authentication, Authorization & Security

### Q3: How is password storage secured?
**Answer:**  
Passwords are never stored in plaintext. We utilize Werkzeug's generate_password_hash and check_password_hash. Under the hood, this uses cryptographic hashing algorithms (such as scrypt or pbkdf2:sha256 with random per-password salts), defending against rainbow table and dictionary attacks.

### Q4: How is Role-Based Access Control (RBAC) enforced?
**Answer:**  
We implement a two-layer security model:
1. **Presentation Layer:** The Jinja2 templates check current_user.role == 'admin' to conditionally display privileged buttons (Add Product, Delete, Register).
2. **Server/Route Layer:** All administrative endpoints are decorated with a custom @admin_required decorator wrapped around @login_required. If an authenticated user with role staff attempts to directly call an admin route via GET or POST, the server aborts with **HTTP 403 Forbidden**.

### Q5: How does CSRF protection work in this app?
**Answer:**  
We configure CSRFProtect(app) from Flask-WTF. Every POST request must supply a valid csrf_token embedded in the form body (via <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">). If the token is missing, expired, or tampered with, Flask-WTF aborts with HTTP 400 Bad Request, preventing cross-site request forgery.

---

## 3. Database Integrity & Concurrency

### Q6: How do you prevent duplicate SKUs under high concurrency?
**Answer:**  
SKU uniqueness is enforced at the database layer via MongoDB's unique index:
\\\python
products.create_index([(\"sku\", ASCENDING)], unique=True)
\\\
Relying on application-level checks alone (ind_one({"sku": ...})) would suffer from race conditions (Time-of-Check to Time-of-Use). With the unique index, MongoDB guarantees uniqueness at the storage engine level and raises DuplicateKeyError, which our route catches and turns into a clear flash message for the user.

### Q7: How are race conditions prevented during Stock IN and Stock OUT?
**Answer:**  
In update_stock(), stock adjustment is performed using MongoDB's atomic $inc operator:
\\\python
products.update_one({\"_id\": oid}, {\"\": {\"quantity\": delta}})
\\\
Because single-document operations in MongoDB are atomic, concurrent stock operations do not suffer from lost updates. Before reducing stock, we verify that current_quantity >= delta to prevent negative balances.

---

## 4. Query Performance & Aggregations

### Q8: What database indexes did you create and why?
**Answer:**  
1. products.sku: Unique index for fast (1)$ lookups and duplicate prevention.
2. products.name: Single-field index for catalog sorting and text regex searches.
3. movements.date: Descending index for rapid retrieval of the latest audit logs on the dashboard.
4. movements.product_id: Single-field index for querying movement history per product.
5. users.username: Unique index for instantaneous login lookups and unique user accounts.

### Q9: How do you compute inventory valuation without scanning all rows in Python?
**Answer:**  
Rather than pulling thousands of documents into Python memory, we execute an aggregation pipeline directly on the database engine:
\\\python
products.aggregate([
    {\"\": {\"_id\": None, \"total\": {\"\": {\"\": [\"\", \"\"]}}}}
])
\\\
This offloads arithmetic computation to MongoDB and returns only a single scalar number over the wire.

---

## 5. Testing & Quality Assurance

### Q10: How do the automated tests ensure production safety?
**Answer:**  
1. **Isolated Test DB:** In 	est_app.py, we set DB_NAME = "logistic_inventory_test". A session fixture verifies this name and aborts immediately if pointed at production.
2. **Fresh Fixtures:** Collections are wiped before each test (utouse=True fixture), ensuring deterministic, side-effect-free execution.
3. **Index Re-generation:** After session database resets, indexes (including the unique SKU index) are re-created to validate true database constraints during tests.
4. **Coverage:** 22 automated test cases cover authentication, CRUD validation, negative value rejections, stock boundary constraints, and RBAC permissions.
