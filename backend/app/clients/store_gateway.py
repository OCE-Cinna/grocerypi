"""
Common template (interface) for connecting to external supermarkets.

This file defines the basic functions that any supermarket connection (such as
Albert Heijn, Jumbo, or Lidl) must have. Because every store follows this same
template, we can easily switch or add supermarkets without changing how the
main inventory system works.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IStoreGateway(ABC):
    """Template that all supermarket API clients must follow."""

    @abstractmethod
    def get_product_by_gtin(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Finds a product's name, category, and nutrition facts using its barcode number."""
        pass

    @abstractmethod
    def search_product(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches the supermarket's online catalog using a product name or keyword."""
        pass
