"""
Package for the Inventory Service.

Exports InventoryService and its shared instance (inventory_service) for use
by the API routes and the camera scanner.
"""

from app.services.inventory.inventory import InventoryService, inventory_service

__all__ = ["InventoryService", "inventory_service"]
