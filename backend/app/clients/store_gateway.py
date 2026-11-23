"""
Common template (interface) for connecting to external supermarkets.

This file defines the basic functions that any supermarket connection (such as
Albert Heijn, Jumbo, Lidl, or Open Food Facts) must have. Because every store
follows this same template, we can easily switch or add supermarkets without
changing how the main inventory service works.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IStoreGateway(ABC):
    """Template that all supermarket and product catalog API clients must follow."""

    @abstractmethod
    def lookup_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Finds a product's name, category, store tag, and nutrition facts using its barcode."""
        pass

    def get_product_by_gtin(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Alias for lookup_by_barcode so existing GTIN callers work identically."""
        return self.lookup_by_barcode(barcode)

    @abstractmethod
    def search_product(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches the supermarket's online catalog using a product name or keyword."""
        pass

    @abstractmethod
    def sync_cart(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepares or sends a list of recommended restock items to the supermarket's
        shopping list or deep-link basket without risking automated account bans.
        """
        pass
