"""
Albert Heijn & Jumbo Supermarket Gateway for GroceryPi.

Implements the IStoreGateway interface for Albert Heijn product lookups and
safe direct web/app cart deep-link synchronization (avoiding unofficial bot
login scraping that could trigger supermarket account bans).
"""

from typing import Any, Dict, List, Optional
import urllib.parse

from app.clients.store_gateway import IStoreGateway
from app.services.ah_client import AHClient, get_ah_client


class AHStoreGateway(AHClient, IStoreGateway):
    """
    Concrete IStoreGateway implementation for Albert Heijn.
    Inherits AH mobile catalog lookup and local JSON caching from AHClient,
    and adds lookup_by_barcode() and safe web/app cart deep-link building.
    """

    def lookup_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Looks up a product in Albert Heijn by its GTIN/EAN barcode."""
        return self.get_product_by_gtin(barcode)

    def sync_cart(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a direct, anti-ban-safe Albert Heijn shopping list / search sync
        payload and deep-link URL for the recommended AH items.
        """
        names = [str(i.get("name") or "").strip() for i in items if i.get("name")]
        search_query = urllib.parse.quote(", ".join(names[:8])) if names else ""
        web_url = (
            f"https://www.ah.nl/zoeken?query={urllib.parse.quote(names[0])}"
            if names
            else "https://www.ah.nl/mijnlijst"
        )
        return {
            "store": "AH",
            "mode": "direct_web_and_app_list",
            "synced_count": len(items),
            "checkout_url": web_url,
            "app_deeplink": f"appie://shoppinglist?items={search_query}",
            "items": names,
        }


class JumboStoreGateway(IStoreGateway):
    """
    Concrete IStoreGateway implementation for Jumbo Supermarkten.
    Provides safe web/app shopping list deep-links for Jumbo items.
    """

    def lookup_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Delegates barcode lookup to the shared Open Food Facts / AH resolver."""
        return get_ah_client().get_product_from_openfoodfacts(barcode)

    def search_product(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches for a product using the shared catalog lookup."""
        return get_ah_client().search_product(query)

    def sync_cart(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Builds a direct, anti-ban-safe Jumbo web/app shopping list payload."""
        names = [str(i.get("name") or "").strip() for i in items if i.get("name")]
        web_url = (
            f"https://www.jumbo.com/producten/?searchType=keyword&searchTerms={urllib.parse.quote(names[0])}"
            if names
            else "https://www.jumbo.com/lijstjes"
        )
        return {
            "store": "Jumbo",
            "mode": "direct_web_and_app_list",
            "synced_count": len(items),
            "checkout_url": web_url,
            "app_deeplink": "jumbo://shoppinglist",
            "items": names,
        }
