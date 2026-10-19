"""
db.py — MongoDB connection module.

Loads MONGO_URI and DB_NAME from .env, establishes a PyMongo client,
and exposes collection references:
  - `products`   : stores product/inventory records (unique index on `sku`, index on `name`)
  - `movements`  : stores stock-in / stock-out movement events (index on `date`, `product_id`)
  - `users`      : stores user accounts with role ("admin" or "staff") (unique index on `username`)
  - `suppliers`  : stores suppliers
  - `warehouses` : stores warehouses
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = os.getenv("DB_NAME",   "logistic_inventory")

# Create the MongoClient
client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

# Collection references
products   = db["products"]
movements  = db["movements"]
users      = db["users"]
suppliers  = db["suppliers"]
warehouses = db["warehouses"]

# Ensure indexes
products.create_index([("sku", ASCENDING)], unique=True)
products.create_index([("name", ASCENDING)])
movements.create_index([("date", DESCENDING)])
movements.create_index([("product_id", ASCENDING)])
users.create_index([("username", ASCENDING)], unique=True)
