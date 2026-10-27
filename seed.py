"""
seed.py — Populate the database with realistic sample data.

Products  : 10 items across Equipment, Packaging, Safety categories.
            3 items are deliberately below their reorder level.
Movements : 5 sample IN/OUT events linked to the inserted products.

Usage:
    python seed.py           (with venv active)
    .\venv\Scripts\python.exe seed.py
"""

from datetime import datetime, timezone

from db import movements, products

# ── Sample products ──────────────────────────────────────────────────────────

PRODUCTS = [
    # ── Equipment ──────────────────────────────────────────────────────────
    {
        "name":          "Forklift Battery Pack",
        "sku":           "EQUIP-001",
        "category":      "Equipment",
        "quantity":      5,
        "reorder_level": 3,
        "price":         1250.00,
        "supplier":      "PowerCell Ltd.",
        "location":      "Warehouse A — Shelf 1",
        "created_at":    datetime.now(timezone.utc),
    },
    {
        "name":          "Pallet Jack",
        "sku":           "EQUIP-002",
        "category":      "Equipment",
        "quantity":      2,            # ⚠ below reorder_level (5)
        "reorder_level": 5,
        "price":         340.00,
        "supplier":      "LiftPro Supplies",
        "location":      "Warehouse A — Bay 3",
        "created_at":    datetime.now(timezone.utc),
    },
    {
        "name":          "Barcode Scanner",
        "sku":           "EQUIP-003",
        "category":      "Equipment",
        "quantity":      12,
        "reorder_level": 5,
        "price":         180.50,
        "supplier":      "TechScan Inc.",
        "location":      "Office — Cabinet 2",
        "created_at":    datetime.now(timezone.utc),
    },
    {
        "name":          "Thermal Label Printer",
        "sku":           "EQUIP-004",
        "category":      "Equipment",
        "quantity":      4,
        "reorder_level": 2,
        "price":         420.00,
        "supplier":      "TechScan Inc.",
        "location":      "Office — Desk 5",
        "created_at":    datetime.now(timezone.utc),
    },
    # ── Packaging ──────────────────────────────────────────────────────────
    {
        "name":          "Stretch Wrap Film (500 m roll)",
        "sku":           "PACK-001",
        "category":      "Packaging",
        "quantity":      80,
        "reorder_level": 50,
        "price":         22.00,
        "supplier":      "PackRight Co.",
        "location":      "Warehouse B — Shelf 5",
        "created_at":    datetime.now(timezone.utc),
    },
    {
        "name":          "Cardboard Box 60×40×40 cm",
        "sku":           "PACK-002",
        "category":      "Packaging",
        "quantity":      30,           # ⚠ below reorder_level (100)
        "reorder_level": 100,
        "price":         3.50,
        "supplier":      "BoxWorld",
        "location":      "Warehouse B — Bay 1",
        "created_at":    datetime.now(timezone.utc),
    },
    {
        "name":          "Bubble Wrap Roll (50 m)",
        "sku":           "PACK-003",
        "category":      "Packaging",
        "quantity":      60,
        "reorder_level": 30,
        "price":         18.75,
        "supplier":      "PackRight Co.",
        "location":      "Warehouse B — Shelf 6",
        "created_at":    datetime.now(timezone.utc),
    },
    # ── Safety ─────────────────────────────────────────────────────────────
    {
        "name":          "Hard Hat (Yellow)",
        "sku":           "SAFE-001",
        "category":      "Safety",
        "quantity":      25,
        "reorder_level": 10,
        "price":         14.99,
        "supplier":      "SafeGuard Gear",
        "location":      "Safety Room — Locker A",
        "created_at":    datetime.now(timezone.utc),
    },
    {
        "name":          "High-Vis Vest (L)",
        "sku":           "SAFE-002",
        "category":      "Safety",
        "quantity":      8,            # ⚠ below reorder_level (15)
        "reorder_level": 15,
        "price":         9.99,
        "supplier":      "SafeGuard Gear",
        "location":      "Safety Room — Locker B",
        "created_at":    datetime.now(timezone.utc),
    },
    {
        "name":          "Safety Gloves (pair)",
        "sku":           "SAFE-003",
        "category":      "Safety",
        "quantity":      50,
        "reorder_level": 20,
        "price":         5.49,
        "supplier":      "WorkSafe Supplies",
        "location":      "Safety Room — Bin 3",
        "created_at":    datetime.now(timezone.utc),
    },
]

# ── Sample movements (sku, kind, qty, note) ──────────────────────────────────

MOVEMENTS_SEED = [
    ("EQUIP-001", "IN",  3,  "Monthly restock from PowerCell"),
    ("PACK-002",  "OUT", 20, "Shipment dispatched to Client A"),
    ("SAFE-002",  "OUT", 5,  "Issued to field team — Zone C"),
    ("PACK-001",  "IN",  50, "Bulk order received from PackRight"),
    ("EQUIP-002", "OUT", 1,  "Deployed to Loading Dock 2"),
]


def seed():
    # Clear existing data to allow re-running cleanly
    products.delete_many({})
    movements.delete_many({})
    print("🗑  Cleared existing products and movements.")

    # Insert products and capture their new _id values
    result   = products.insert_many(PRODUCTS)
    inserted = result.inserted_ids
    print(f"✅ Inserted {len(inserted)} products.")

    # Build sku → (_id, name) map for movement linking
    sku_map = {
        prod["sku"]: (oid, prod["name"])
        for prod, oid in zip(PRODUCTS, inserted)
    }

    # Build and insert movement documents
    movement_docs = [
        {
            "product_id":   sku_map[sku][0],
            "product_name": sku_map[sku][1],
            "type":         kind,
            "qty":          qty,
            "date":         datetime.now(timezone.utc),
            "note":         note,
            "user":         "seed",  # Marks these as automatically seeded records
        }
        for sku, kind, qty, note in MOVEMENTS_SEED
    ]
    movements.insert_many(movement_docs)
    print(f"✅ Inserted {len(movement_docs)} sample movements.")

    print("\n🌱 Seed complete!")
    print("   Run the app and visit http://127.0.0.1:5000")


if __name__ == "__main__":
    seed()
