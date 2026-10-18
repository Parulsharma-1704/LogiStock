"""
app.py — Logistic Inventory Flask application (Step 2: full backend).

Routes
------
GET  /                         Dashboard: stats, low-stock, recent movements
GET  /products                 Product list with search (?q=) and category filter
GET  /products/add             Show add form
POST /products/add             Create a new product
GET  /products/edit/<id>       Show edit form
POST /products/edit/<id>       Update an existing product
POST /products/delete/<id>     Delete a product
POST /stock/<id>/<kind>        Stock IN or OUT; logs a movement
GET  /movements                Full movement history, newest first
"""

import os
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template,
                   request, url_for)
from pymongo.errors import DuplicateKeyError

from db import client, movements, products

# ── App setup ────────────────────────────────────────────────────────────────

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-dev-key")

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

    # ── Numeric fields ──
    try:
        quantity = int(form.get("quantity", ""))
        if quantity < 0:
            errors.append("Quantity cannot be negative.")
    except (ValueError, TypeError):
        quantity = None
        errors.append("Quantity must be a whole number.")

    try:
        reorder_level = int(form.get("reorder_level", ""))
        if reorder_level < 0:
            errors.append("Reorder level cannot be negative.")
    except (ValueError, TypeError):
        reorder_level = None
        errors.append("Reorder level must be a whole number.")

    try:
        price = float(form.get("price", ""))
        if price < 0:
            errors.append("Price cannot be negative.")
    except (ValueError, TypeError):
        price = None
        errors.append("Price must be a valid number.")

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


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
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
def add_product():
    """
    GET  — Render empty add form.
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
def edit_product(product_id):
    """
    GET  — Render form pre-filled with existing product data.
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
def delete_product(product_id):
    """
    POST only — Delete a product by ID.
    GET requests to this URL will 405 (Method Not Allowed).
    """
    product = get_product_or_404(product_id)
    products.delete_one({"_id": product["_id"]})
    flash(f"Product '{product['name']}' has been deleted.", "success")
    return redirect(url_for("product_list"))


@app.route("/stock/<product_id>/<kind>", methods=["POST"])
def update_stock(product_id, kind):
    """
    POST — Adjust stock quantity and record a movement document.
    kind : 'IN'  — increase quantity ($inc positive delta)
           'OUT' — decrease quantity ($inc negative delta)
                   Blocked when requested qty > current stock.
    Movement fields: product_id, product_name, type, qty, date, note.
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

    # Log the movement
    movements.insert_one({
        "product_id":   product["_id"],
        "product_name": product["name"],
        "type":         kind,
        "qty":          qty,
        "date":         datetime.now(timezone.utc),
        "note":         note,
    })

    flash(
        f"Stock {kind}: {qty} unit(s) recorded for '{product['name']}'.",
        "success",
    )
    return redirect(url_for("product_list"))


@app.route("/movements")
def movement_history():
    """Full movement log, sorted newest-first."""
    all_movements = list(movements.find().sort("date", -1))
    return render_template("movements.html", movements=all_movements)


# ── Error handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ping MongoDB on startup so a connection failure is caught immediately
    try:
        client.admin.command("ping")
        print("✅ MongoDB connected successfully.")
    except Exception as exc:
        print(f"❌ MongoDB connection failed: {exc}")

    app.run(debug=True)
