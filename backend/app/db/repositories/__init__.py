"""
Package for database repositories.

Repositories handle all reading and writing to the SQLite database tables so
the rest of the app does not need to write raw database queries.
"""

from app.db.repositories.inventory_repository import InventoryRepository
from app.db.repositories.product_repository import ProductRepository

__all__ = ["ProductRepository", "InventoryRepository"]
