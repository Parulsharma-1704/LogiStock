# coding: utf-8
"""
tests/test_app.py -- Automated tests for LogiStock (Step 5).

Database : logistic_inventory_test  (NEVER the real DB)
Framework: pytest + Flask test client

Run with:
    .\\venv\\Scripts\\python.exe -m pytest tests/ -v

Output legend:
    PASSED  -- assertion succeeded
    FAILED  -- assertion failed (reason printed below the line)
    ERROR   -- exception during fixture setup/teardown
    SKIPPED -- route not present (CSV test only)
"""

import os
import pytest
from bson import ObjectId
from werkzeug.security import generate_password_hash

# ---- point at the TEST DB before any import touches db.py ----
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/")
os.environ["DB_NAME"] = "logistic_inventory_test"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["WTF_CSRF_ENABLED"] = "False"

import db as db_module          # noqa: E402
from app import app as flask_app  # noqa: E402


# ===========================================================================
#  Fixtures
# ===========================================================================

@pytest.fixture(scope="session", autouse=True)
def test_db_setup():
    """Drop + recreate test DB at the start and end of the session."""
    name = db_module.DB_NAME
    assert name == "logistic_inventory_test", (
        f"Safety guard: DB_NAME is {name!r}. Tests aborted to protect real data."
    )
    db_module.client.drop_database(name)
    # Re-create indexes after dropping database
    db_module.products.create_index([("sku", 1)], unique=True)
    db_module.products.create_index([("name", 1)])
    db_module.movements.create_index([("date", -1)])
    db_module.movements.create_index([("product_id", 1)])
    db_module.users.create_index([("username", 1)], unique=True)
    yield
    db_module.client.drop_database(name)


@pytest.fixture(autouse=True)
def clean_collections():
    """Wipe every collection before each individual test."""
    for col in (db_module.products, db_module.movements, db_module.users):
        col.delete_many({})
    yield


@pytest.fixture()
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def admin_user():
    creds = {"username": "testadmin", "password": "Admin@1234"}
    db_module.users.insert_one({
        "username": creds["username"],
        "password_hash": generate_password_hash(creds["password"]),
        "role": "admin",
    })
    return creds


@pytest.fixture()
def staff_user():
    creds = {"username": "teststaff", "password": "Staff@5678"}
    db_module.users.insert_one({
        "username": creds["username"],
        "password_hash": generate_password_hash(creds["password"]),
        "role": "staff",
    })
    return creds


def do_login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def sample_product(**ov):
    d = {
        "name": "Test Battery",
        "sku": "TEST-001",
        "category": "Equipment",
        "quantity": "10",
        "reorder_level": "5",
        "price": "500.00",
        "supplier": "TestCo",
        "location": "WH-A",
    }
    d.update(ov)
    return d


# ===========================================================================
#  Auth
# ===========================================================================

class TestAuth:

    def test_login_success(self, client, admin_user):
        r = do_login(client, admin_user["username"], admin_user["password"])
        assert r.status_code == 200
        assert b"Dashboard" in r.data or b"LogiStock" in r.data

    def test_login_wrong_password(self, client, admin_user):
        r = do_login(client, admin_user["username"], "badpass")
        assert r.status_code == 200
        assert b"Invalid" in r.data

    def test_login_unknown_user(self, client):
        r = do_login(client, "nobody", "x")
        assert r.status_code == 200
        assert b"Invalid" in r.data

    def test_landing_page_public(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_logged_out_redirect(self, client):
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_logout(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        client.get("/logout", follow_redirects=True)
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]


# ===========================================================================
#  Product CRUD
# ===========================================================================

class TestProductCRUD:

    def test_add_product_success(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        r = client.post("/products/add", data=sample_product(), follow_redirects=True)
        assert r.status_code == 200
        assert db_module.products.count_documents({}) == 1

    def test_duplicate_sku_rejected(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        client.post("/products/add", data=sample_product(), follow_redirects=True)
        r = client.post("/products/add", data=sample_product(), follow_redirects=True)
        assert db_module.products.count_documents({}) == 1
        assert b"already exists" in r.data or b"SKU" in r.data

    def test_negative_quantity_rejected(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        client.post("/products/add", data=sample_product(quantity="-5"), follow_redirects=True)
        assert db_module.products.count_documents({}) == 0

    def test_negative_price_rejected(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        client.post("/products/add", data=sample_product(price="-1.00"), follow_redirects=True)
        assert db_module.products.count_documents({}) == 0

    def test_invalid_objectid_returns_404(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        assert client.get("/products/edit/not-a-valid-id").status_code == 404

    def test_nonexistent_product_returns_404(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        assert client.get(f"/products/edit/{ObjectId()}").status_code == 404


# ===========================================================================
#  Stock movements
# ===========================================================================

class TestStockMovements:

    def _ins(self, qty=10, reorder=5):
        r = db_module.products.insert_one({
            "name": "Battery", "sku": "B-001", "category": "Equipment",
            "quantity": qty, "reorder_level": reorder, "price": 500.0,
            "supplier": "Co", "location": "A",
        })
        return db_module.products.find_one({"_id": r.inserted_id})

    def test_stock_in_increases_quantity_and_logs_movement(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        p = self._ins(qty=10)
        client.post(f"/stock/{p['_id']}/IN", data={"qty": "5", "note": "Restock"}, follow_redirects=True)
        assert db_module.products.find_one({"_id": p["_id"]})["quantity"] == 15
        mvs = list(db_module.movements.find({"product_id": p["_id"]}))
        assert len(mvs) == 1 and mvs[0]["type"] == "IN" and mvs[0]["qty"] == 5

    def test_stock_out_decreases_quantity_and_logs_movement(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        p = self._ins(qty=10)
        client.post(f"/stock/{p['_id']}/OUT", data={"qty": "3"}, follow_redirects=True)
        assert db_module.products.find_one({"_id": p["_id"]})["quantity"] == 7
        mvs = list(db_module.movements.find({"product_id": p["_id"]}))
        assert len(mvs) == 1 and mvs[0]["type"] == "OUT" and mvs[0]["qty"] == 3

    def test_stock_out_blocked_when_insufficient(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        p = self._ins(qty=3)
        r = client.post(f"/stock/{p['_id']}/OUT", data={"qty": "10"}, follow_redirects=True)
        assert db_module.products.find_one({"_id": p["_id"]})["quantity"] == 3
        assert db_module.movements.count_documents({"product_id": p["_id"]}) == 0
        assert b"Insufficient" in r.data

    def test_stock_out_exact_quantity_allowed(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        p = self._ins(qty=5)
        client.post(f"/stock/{p['_id']}/OUT", data={"qty": "5"}, follow_redirects=True)
        assert db_module.products.find_one({"_id": p["_id"]})["quantity"] == 0


# ===========================================================================
#  Role access
# ===========================================================================

class TestRoleAccess:

    def test_staff_blocked_from_add_product_get(self, client, staff_user):
        do_login(client, staff_user["username"], staff_user["password"])
        assert client.get("/products/add").status_code == 403

    def test_staff_blocked_from_add_product_post(self, client, staff_user):
        do_login(client, staff_user["username"], staff_user["password"])
        assert client.post("/products/add", data=sample_product()).status_code == 403

    def test_staff_blocked_from_edit_product(self, client, admin_user, staff_user):
        do_login(client, admin_user["username"], admin_user["password"])
        db_module.products.insert_one({"name": "X", "sku": "X-001", "category": "C", "quantity": 1, "reorder_level": 0, "price": 1.0})
        p = db_module.products.find_one({"sku": "X-001"})
        client.get("/logout")
        do_login(client, staff_user["username"], staff_user["password"])
        assert client.get(f"/products/edit/{p['_id']}").status_code == 403

    def test_staff_blocked_from_delete_product(self, client, admin_user, staff_user):
        do_login(client, admin_user["username"], admin_user["password"])
        db_module.products.insert_one({"name": "Y", "sku": "Y-001", "category": "C", "quantity": 1, "reorder_level": 0, "price": 1.0})
        p = db_module.products.find_one({"sku": "Y-001"})
        client.get("/logout")
        do_login(client, staff_user["username"], staff_user["password"])
        assert client.post(f"/products/delete/{p['_id']}").status_code == 403

    def test_staff_can_view_inventory(self, client, staff_user):
        do_login(client, staff_user["username"], staff_user["password"])
        assert client.get("/products").status_code == 200

    def test_staff_can_perform_stock_in(self, client, staff_user):
        do_login(client, staff_user["username"], staff_user["password"])
        db_module.products.insert_one({"name": "Z", "sku": "Z-001", "category": "C", "quantity": 5, "reorder_level": 2, "price": 10.0})
        p = db_module.products.find_one({"sku": "Z-001"})
        client.post(f"/stock/{p['_id']}/IN", data={"qty": "3"}, follow_redirects=True)
        assert db_module.products.find_one({"_id": p["_id"]})["quantity"] == 8


# ===========================================================================
#  Low-stock query
# ===========================================================================

class TestLowStock:

    def test_low_stock_query_returns_correct_items(self):
        db_module.products.insert_many([
            {"name": "A", "sku": "A-001", "category": "C", "quantity": 2,  "reorder_level": 5,  "price": 1.0},
            {"name": "B", "sku": "B-001", "category": "C", "quantity": 5,  "reorder_level": 5,  "price": 1.0},
            {"name": "C", "sku": "C-001", "category": "C", "quantity": 20, "reorder_level": 5,  "price": 1.0},
            {"name": "D", "sku": "D-001", "category": "C", "quantity": 0,  "reorder_level": 10, "price": 1.0},
        ])
        low = list(db_module.products.find(
            {"$expr": {"$lte": ["$quantity", "$reorder_level"]}},
            sort=[("quantity", 1)],
        ))
        skus = {p["sku"] for p in low}
        assert "A-001" in skus
        assert "B-001" in skus
        assert "D-001" in skus
        assert "C-001" not in skus
        assert len(low) == 3


# ===========================================================================
#  CSV export
# ===========================================================================

class TestExport:

    def test_csv_export_returns_text_csv(self, client, admin_user):
        do_login(client, admin_user["username"], admin_user["password"])
        db_module.products.insert_one({
            "name": "Battery Pack", "sku": "BAT-001", "category": "Equipment",
            "quantity": 5, "reorder_level": 2, "price": 1250.0,
            "supplier": "PowerCell", "location": "Shelf 1",
        })
        r = client.get("/export/csv")
        if r.status_code == 404:
            pytest.skip("/export/csv not implemented -- skipping")
        assert r.status_code == 200
        ct = r.headers.get("Content-Type", "")
        assert "text/csv" in ct or "application/csv" in ct
        assert b"name" in r.data.lower() or b"sku" in r.data.lower()
