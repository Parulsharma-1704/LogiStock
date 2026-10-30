"""
app.py — Logistic Inventory Flask application with Authentication & Role Control.

Routes
------
GET  /login                     Show login page
POST /login                     Authenticate user with Werkzeug hash
GET  /logout                    Sign out current user
GET  /register                  Show user registration form (admin only)
POST /register                  Create new user account (admin only)
GET  /                          Dashboard (login required)
GET  /products                  Product list (login required)
GET  /products/add              Add product form (admin only)
POST /products/add              Insert product (admin only)
GET  /products/edit/<id>        Edit product form (admin only)
POST /products/edit/<id>        Update product (admin only)
POST /products/delete/<id>      Delete product (admin only)
POST /stock/<id>/<kind>         Stock IN or OUT; logs movement with user tag (login required)
GET  /movements                 Movement history (login required)
"""

import os
from datetime import datetime, timezone
from functools import wraps

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template,
                   request, url_for)
from flask_wtf.csrf import CSRFProtect
from flask_login import (LoginManager, UserMixin, current_user,
                         login_required, login_user, logout_user)
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash

from db import client, movements, products, users, suppliers, warehouses

# ── App setup ────────────────────────────────────────────────────────────────

load_dotenv()

app = Flask(__name__)

_secret = os.getenv("SECRET_KEY")
if not _secret:
    # Refuse to run silently with a weak key — set SECRET_KEY in your .env
    import warnings
    warnings.warn(
        "SECRET_KEY not set in environment; using an insecure fallback. "
        "Set SECRET_KEY in your .env file before deploying.",
        RuntimeWarning,
        stacklevel=2,
    )
    _secret = "fallback-dev-key-DO-NOT-USE-IN-PRODUCTION"
app.secret_key = _secret

# Enable CSRF protection for all POST forms via Flask-WTF
csrf = CSRFProtect(app)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access LogiStock."
login_manager.login_message_category = "warning"


# ── User model & loader ──────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, doc: dict):
        self.id = str(doc["_id"])
        self.username = doc.get("username", "")
        self.role = doc.get("role", "staff")
        self.doc = doc

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id: str):
    try:
        doc = users.find_one({"_id": ObjectId(user_id)})
        return User(doc) if doc else None
    except Exception:
        return None


def admin_required(f):
    """Decorator to restrict route access strictly to users with role='admin'.
    Returns HTTP 403 Forbidden so tests can assert the status code.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)  # Forbidden — staff users get a 403, not a silent redirect
        return f(*args, **kwargs)
    return decorated_function


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_product_or_404(product_id: str):
    """
    Fetch a product by its string ObjectId.
    Aborts with 404 on an invalid ID format or a missing document.
    """
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        abort(404)

    doc = products.find_one({"_id": oid})
    if doc is None:
        abort(404)
    return doc


def validate_product_form(form) -> tuple:
    """
    Parse and validate the product add/edit HTML form.
    Returns (cleaned_dict, errors_list).
    cleaned_dict is None when there are any errors.
    """
    errors = []

    # ── Text fields ──
    name     = form.get("name",     "").strip()
    sku      = form.get("sku",      "").strip().upper()
    category = form.get("category", "").strip()
    supplier = form.get("supplier", "").strip()
    location = form.get("location", "").strip()

    if not name:
        errors.append("Product name is required.")
    if not sku:
        errors.append("SKU is required.")
    if not category:
        errors.append("Category is required.")

    # ── Numeric: quantity (int >= 0) ──
    raw_qty = form.get("quantity", "").strip()
    try:
        quantity = int(raw_qty)
        if quantity < 0:
            errors.append("Quantity cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Quantity must be a non-negative whole number.")
        quantity = None

    # ── Numeric: reorder_level (int >= 0) ──
    raw_reorder = form.get("reorder_level", "").strip()
    try:
        reorder_level = int(raw_reorder)
        if reorder_level < 0:
            errors.append("Reorder level cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Reorder level must be a non-negative whole number.")
        reorder_level = None

    # ── Numeric: price (float >= 0.0) ──
    raw_price = form.get("price", "").strip()
    try:
        price = float(raw_price)
        if price < 0.0:
            errors.append("Price cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Price must be a valid non-negative number.")
        price = None

    if errors:
        return None, errors

    return {
        "name":          name,
        "sku":           sku,
        "category":      category,
        "quantity":      quantity,
        "reorder_level": reorder_level,
        "price":         price,
        "supplier":      supplier,
        "location":      location,
    }, []


# ── Auth Routes ──────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("login.html")

        user_doc = users.find_one({"username": username})
        if user_doc and check_password_hash(user_doc.get("password_hash", ""), password):
            login_user(User(user_doc))
            flash(f"Welcome back, {username}!", "success")
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
                next_page = url_for("dashboard")
            return redirect(next_page)

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
@login_required
@admin_required
def register():
    """Admin-only route to create new user accounts."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role     = request.form.get("role", "staff").strip().lower()

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if role not in ("admin", "staff"):
            errors.append("Role must be 'admin' or 'staff'.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("register.html")

        try:
            users.insert_one({
                "username": username,
                "password_hash": generate_password_hash(password),
                "role": role,
                "created_at": datetime.now(timezone.utc),
            })
            flash(f"User '{username}' created successfully with role '{role.upper()}'.", "success")
            return redirect(url_for("register"))
        except DuplicateKeyError:
            flash(f"Username '{username}' already exists. Please choose a different username.", "error")
            return render_template("register.html")

    return render_template("register.html")


# ── Landing & Operations Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    """
    Public NFT-marketplace-style landing page.
    Queries top products by quantity and top suppliers from MongoDB.
    Logged-in users still see the landing page with 'Go to Dashboard'.
    """
    top_products = list(
        products.find({}, {
            "name": 1, "sku": 1, "quantity": 1, "price": 1,
            "category": 1, "location": 1, "reorder_level": 1
        })
        .sort("quantity", -1)
        .limit(5)
    )

    # Fetch suppliers from collection or fallback to distinct suppliers from products
    supplier_docs = list(suppliers.find({}, {"name": 1, "contact": 1, "location": 1}).limit(8))
    if not supplier_docs:
        distinct_suppliers = [s for s in products.distinct("supplier") if s]
        supplier_docs = [{"name": s} for s in distinct_suppliers[:8]]

    total_products_count = products.count_documents({})
    total_movements_count = movements.count_documents({})

    units_result = list(products.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
    ]))
    total_units = units_result[0]["total"] if units_result else 0

    return render_template(
        "landing.html",
        top_products=top_products,
        suppliers=supplier_docs,
        total_products=total_products_count,
        total_movements=total_movements_count,
        total_units=total_units,
    )


@app.route("/dashboard")
@login_required
def dashboard():
    """
    Dashboard summary:
    - Total product count
    - Total inventory value  (aggregation: sum of quantity * price)
    - Low-stock items        (quantity <= reorder_level)
    - Stock by category      (aggregation: group by category)
    - 5 most recent movements
    """
    total_products = products.count_documents({})

    # Total inventory value via aggregation
    value_result = list(products.aggregate([
        {"$group": {
            "_id": None,
            "total": {"$sum": {"$multiply": ["$quantity", "$price"]}}
        }}
    ]))
    total_value = value_result[0]["total"] if value_result else 0.0

    # Items where quantity is at or below the reorder threshold
    low_stock = list(products.find(
        {"$expr": {"$lte": ["$quantity", "$reorder_level"]}},
        sort=[("quantity", 1)]
    ))

    # Per-category totals
    stock_by_category = list(products.aggregate([
        {"$group": {
            "_id":       "$category",
            "total_qty": {"$sum": "$quantity"},
            "count":     {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]))

    # Five most recent movements
    recent_movements = list(movements.find().sort("date", -1).limit(5))

    # Total units across all products (for stat card)
    units_result = list(products.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
    ]))
    total_units = units_result[0]["total"] if units_result else 0

    # Top 5 products by quantity — strip ObjectId so tojson works cleanly
    top5_by_qty = [
        {"name": p["name"], "quantity": p["quantity"]}
        for p in products.find({}, {"name": 1, "quantity": 1}).sort("quantity", -1).limit(5)
    ]

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_value=total_value,
        total_units=total_units,
        low_stock=low_stock,
        stock_by_category=stock_by_category,
        recent_movements=recent_movements,
        top5_by_qty=top5_by_qty,
    )


@app.route("/products")
@login_required
def product_list():
    """
    Product listing with optional:
    - ?q=<text>        case-insensitive search on name or SKU
    - ?category=<cat>  filter by category
    Low-stock rows are highlighted in the template.
    """
    q        = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = {}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"sku":  {"$regex": q, "$options": "i"}},
        ]
    if category:
        query["category"] = category

    all_products = list(products.find(query).sort("name", 1))
    categories   = products.distinct("category")

    return render_template(
        "products.html",
        products=all_products,
        q=q,
        selected_category=category,
        categories=categories,
    )


@app.route("/products/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    """
    GET  — Render empty add form (admin only).
    POST — Validate input, insert new product, flash result.
           On duplicate SKU shows a friendly DuplicateKeyError message.
    """
    if request.method == "POST":
        data, errors = validate_product_form(request.form)

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("product_form.html", product=request.form, action="add")

        data["created_at"] = datetime.now(timezone.utc)

        try:
            products.insert_one(data)
            flash(f"Product '{data['name']}' added successfully.", "success")
            return redirect(url_for("product_list"))
        except DuplicateKeyError:
            flash(f"SKU '{data['sku']}' already exists. Please use a unique SKU.", "error")
            return render_template("product_form.html", product=request.form, action="add")

    return render_template("product_form.html", product={}, action="add")


@app.route("/products/edit/<product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id):
    """
    GET  — Render form pre-filled with existing product data (admin only).
    POST — Validate, update with $set, flash result.
           Preserves created_at; skips updating it on edit.
    """
    product = get_product_or_404(product_id)

    if request.method == "POST":
        data, errors = validate_product_form(request.form)

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("product_form.html", product=request.form,
                                   action="edit", product_id=product_id)

        try:
            products.update_one({"_id": product["_id"]}, {"$set": data})
            flash(f"Product '{data['name']}' updated successfully.", "success")
            return redirect(url_for("product_list"))
        except DuplicateKeyError:
            flash(f"SKU '{data['sku']}' is already used by another product.", "error")
            return render_template("product_form.html", product=request.form,
                                   action="edit", product_id=product_id)

    return render_template("product_form.html", product=product,
                           action="edit", product_id=str(product["_id"]))


@app.route("/products/delete/<product_id>", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    """
    POST only — Delete a product by ID (admin only).
    GET requests to this URL will 405 (Method Not Allowed).
    """
    product = get_product_or_404(product_id)
    products.delete_one({"_id": product["_id"]})
    flash(f"Product '{product['name']}' has been deleted.", "success")
    return redirect(url_for("product_list"))


@app.route("/stock/<product_id>/<kind>", methods=["POST"])
@login_required
def update_stock(product_id, kind):
    """
    POST — Adjust stock quantity and record a movement document with the current user.
    kind : 'IN'  — increase quantity ($inc positive delta)
           'OUT' — decrease quantity ($inc negative delta)
                   Blocked when requested qty > current stock.
    Movement fields: product_id, product_name, type, qty, date, note, user.
    """
    kind = kind.upper()
    if kind not in ("IN", "OUT"):
        flash("Invalid movement type. Use IN or OUT.", "error")
        return redirect(url_for("product_list"))

    product = get_product_or_404(product_id)

    # Validate qty from form
    try:
        qty = int(request.form.get("qty", ""))
        if qty <= 0:
            raise ValueError("Must be positive")
    except (ValueError, TypeError):
        flash("Stock quantity must be a positive whole number.", "error")
        return redirect(url_for("product_list"))

    note = request.form.get("note", "").strip()

    # Prevent overdraft on OUT movements
    if kind == "OUT" and product["quantity"] < qty:
        flash(
            f"Insufficient stock for '{product['name']}'. "
            f"Available: {product['quantity']}, Requested: {qty}.",
            "error",
        )
        return redirect(url_for("product_list"))

    delta = qty if kind == "IN" else -qty
    products.update_one({"_id": product["_id"]}, {"$inc": {"quantity": delta}})

    # Log the movement with current authenticated user
    user_name = current_user.username if current_user.is_authenticated else "system"
    movements.insert_one({
        "product_id":   product["_id"],
        "product_name": product["name"],
        "type":         kind,
        "qty":          qty,
        "date":         datetime.now(timezone.utc),
        "note":         note,
        "user":         user_name,
    })

    flash(
        f"Stock {kind}: {qty} unit(s) recorded for '{product['name']}'.",
        "success",
    )
    return redirect(url_for("product_list"))


@app.route("/movements")
@login_required
def movement_history():
    """Full movement log, sorted newest-first."""
    all_movements = list(movements.find().sort("date", -1))
    return render_template("movements.html", movements=all_movements)


# ── Error handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    """Return a plain-text 403 so API callers and tests see the status code."""
    return "403 Forbidden — Admin access required.", 403


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ping MongoDB on startup so a connection failure is caught immediately
    try:
        client.admin.command("ping")
        print("✅ MongoDB connected successfully.")
    except Exception as exc:
        print(f"❌ MongoDB connection failed: {exc}")

    app.run(debug=True)
