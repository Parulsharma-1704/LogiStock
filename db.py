"""
db.py — MongoDB connection module.

Loads MONGO_URI and DB_NAME from .env, establishes a PyMongo client,
and exposes two collection references:
  - `products`   : stores product/inventory records (unique index on `sku`)
  - `movements`  : stores stock-in / stock-out movement events
"""

import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = os.getenv("DB_NAME",   "logistic_inventory")

# Create the MongoClient (connection is lazy — actually connects on first use)
client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

# Collection references
products  = db["products"]
movements = db["movements"]

# Ensure SKU is unique across all product documents
products.create_index([("sku", ASCENDING)], unique=True)
