# LogiStock — Logistic Inventory Management System

LogiStock is a production-ready, security-hardened inventory and logistics tracking web application built with **Flask**, **PyMongo**, and **MongoDB**. It features a modern dark-mode glassmorphic interface, role-based access control (Admin / Staff), live stock-in/out auditing, reorder-level alerts, and automated pytest test coverage.

---

## Key Features

- **Role-Based Access Control (RBAC):**
  - **Admin:** Full inventory CRUD, user registration, stock adjustments, and deletion privileges.
  - **Staff:** Read inventory, perform stock adjustments (IN/OUT), and view audit movements. Admin-exclusive routes are protected at both UI and server level (HTTP 403).
- **Inventory & SKU Management:**
  - Strict validation preventing negative quantities and negative prices.
  - Unique SKU enforcement guaranteed via MongoDB unique indexing and handled gracefully.
- **Stock Movements & Audit Trails:**
  - Real-time stock increments and decrements.
  - Safeguards against overdrafts (insufficient stock validation).
  - Every transaction logs quantity delta, movement type, user, notes, and UTC timestamp.
- **Interactive Dashboard & Low Stock Alerts:**
  - Key operational KPIs: Total products, warehouse stock units, total inventory valuation ($).
  - Category distribution breakdowns and top products by quantity.
  - Highlighted low-stock warnings when quantity <= reorder_level.
- **Security & Integrity:**
  - CSRF protection across all forms and modals via Flask-WTF.
  - Passwords hashed with werkzeug.security (scrypt / pbkdf2).
  - All credentials and secrets configured strictly via .env.
  - HTTP-only and SameSite session cookies.

---

## Tech Stack

- **Backend:** Python 3.10+ / Flask 3.1
- **Database:** MongoDB 6.0+ via PyMongo 4.19
- **Authentication & Forms:** Flask-Login, Flask-WTF, WTForms
- **Testing:** Pytest (with dedicated isolated test database logistic_inventory_test)
- **Styling:** Custom Vanilla CSS Dark Glassmorphism Design System

---

## Directory Structure

\\\
logisticInventory/
├── app.py                 # Core application routes & logic
├── db.py                  # PyMongo connection, collections, and index definitions
├── seed.py                # Database seeder with sample warehouses, suppliers & items
├── create_admin.py        # CLI utility for creating initial admin accounts
├── requirements.txt       # Pinned production and test dependencies
├── .env.example           # Example environment variable template
├── .gitignore             # Standard Python and environment exclusions
├── MANUAL_TESTING.md      # Test matrix and manual QA scenarios
├── DEMO_SCRIPT.md         # 5-minute presentation & demo walkthrough
├── VIVA_PREP.md           # Technical viva Q&A and architecture deep dive
├── static/                # CSS styling, glassmorphism assets, and scripts
├── templates/             # Jinja2 HTML templates
└── tests/
    └── test_app.py        # Automated pytest suite (CRUD, Auth, RBAC, Movements)
\\\

---

## Quickstart & Installation

### 1. Prerequisites
- Python 3.10 or higher
- MongoDB service running locally on \mongodb://localhost:27017/\ (or MongoDB Atlas URI)

### 2. Setup Virtual Environment
\\\powershell
# Clone or navigate to the directory
cd logisticInventory

# Create virtual environment
python -m venv venv

# Activate on Windows
.\\venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
\\\

### 3. Configure Environment Variables
Copy \.env.example\ to \.env\:
\\\powershell
Copy-Item .env.example .env
\\\
Edit \.env\ if needed:
\\\ini
MONGO_URI=mongodb://localhost:27017/
DB_NAME=logistic_inventory
SECRET_KEY=generate_a_secure_random_key_here
\\\

### 4. Seed the Database
Initialize collections, indexes, and sample data:
\\\powershell
.\\venv\\Scripts\\python.exe seed.py
.\\venv\\Scripts\\python.exe create_admin.py
\\\
Default credentials created:
- **Admin User:** \dmin\ / \Admin@123\
- **Staff User:** \staff\ / \Staff@123\

### 5. Run the Application
\\\powershell
.\\venv\\Scripts\\python.exe app.py
\\\
Access the dashboard at: **\http://127.0.0.1:5000\**

---

## Running Automated Tests

LogiStock includes a full suite of automated unit and integration tests. All tests run against an isolated database (\logistic_inventory_test\) and **never touch production data**.

\\\powershell
.\\venv\\Scripts\\python.exe -m pytest tests/ -v
\\\

---

## Routes & API Reference

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET, POST | \/login\ | Sign in with username and password | Public |
| GET | \/logout\ | Sign out current user | Authenticated |
| GET, POST | \/register\ | Register a new user (admin / staff) | Admin Only |
| GET | \/\ | Operational dashboard with KPIs and analytics | Authenticated |
| GET | \/products\ | Filterable inventory catalog with search | Authenticated |
| GET, POST | \/products/add\ | Add a new inventory product | Admin Only |
| GET, POST | \/products/edit/<id>\ | Update existing product details | Admin Only |
| POST | \/products/delete/<id>\| Remove a product | Admin Only |
| POST | \/stock/<id>/<kind>\ | Adjust stock level (\kind\: IN or OUT) | Authenticated |
| GET | \/movements\ | Stock movement history & audit trail | Authenticated |
