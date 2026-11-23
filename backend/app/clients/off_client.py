"""
Open Food Facts backup product client and multi-store brand tagger for GroceryPi.

When a scanned barcode is not sold at Albert Heijn (for example, products bought
at Jumbo, Lidl, or international brand items), this client queries the Dutch
Open Food Facts database (`nl.openfoodfacts.org`), selects only Dutch or English
product titles, and automatically detects whether the product belongs to Jumbo
or Lidl based on its store and private-label brand tags.
"""

import json
import logging
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from app.clients.store_gateway import IStoreGateway
from app.models import PreferredStore
from app.services.ah_client import (
    clean_product_name_and_brand,
    detect_is_frozen,
    infer_preferred_store_from_off,
    map_category,
    select_dutch_or_english_name,
)

logger = logging.getLogger("grocerypi.off_client")


class OpenFoodFactsClient(IStoreGateway):
    """
    Connects to the public Open Food Facts API to look up barcodes from any
    supermarket and automatically tag Jumbo and Lidl products.
    """

    BASE_URL = "https://nl.openfoodfacts.org"

    def lookup_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Looks up a barcode in Open Food Facts, strictly keeping Dutch or English
        names and auto-detecting Jumbo or Lidl store tags.
        """
        clean_barcode = barcode.strip()
        url = f"{self.BASE_URL}/api/v2/product/{clean_barcode}.json?lc=nl"
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "GroceryPi/2.0 (Raspberry Pi Touchscreen Kiosk)",
                    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == 1 and "product" in data:
                    return self.parse_off_product(clean_barcode, data["product"])
        except Exception as e:
            logger.debug(f"OpenFoodFacts lookup failed for {clean_barcode}: {e}")
        return None

    @staticmethod
    def parse_off_product(clean_barcode: str, prod: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extracts clean Dutch/English product details, store tags (Jumbo/Lidl/AH),
        Nutri-Score, vegan/vegetarian flags, frozen status, and per-100g macros
        from an Open Food Facts product record.
        """
        raw_brand = prod.get("brands")
        selected_title = select_dutch_or_english_name(prod)
        if not selected_title:
            if raw_brand:
                selected_title = f"{raw_brand.split(',')[0].strip()} Product"
            else:
                return None

        clean_name, clean_brand = clean_product_name_and_brand(selected_title, raw_brand)

        nutriscore = (prod.get("nutriscore_grade") or "").upper() or None
        if nutriscore and nutriscore not in ["A", "B", "C", "D", "E"]:
            nutriscore = None

        tags = [str(t).lower() for t in prod.get("labels_tags", [])]
        is_vegan = any("vegan" in t for t in tags)
        is_veg = is_vegan or any("vegetarian" in t for t in tags)

        nutriments = prod.get("nutriments", {})
        nutrition = {
            "energy_kj": float(nutriments.get("energy-kj_100g") or 0.0),
            "energy_kcal": float(
                nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g") or 0.0
            ),
            "fat_grams": float(nutriments.get("fat_100g") or 0.0),
            "saturated_fat_grams": float(nutriments.get("saturated-fat_100g") or 0.0),
            "carbohydrate_grams": float(nutriments.get("carbohydrates_100g") or 0.0),
            "sugar_grams": float(nutriments.get("sugars_100g") or 0.0),
            "fiber_grams": float(nutriments.get("fiber_100g") or 0.0),
            "protein_grams": float(nutriments.get("proteins_100g") or 0.0),
            "salt_grams": float(nutriments.get("salt_100g") or 0.0),
        }

        cat_tags_list = [str(c) for c in (prod.get("categories_tags") or [])]
        en_or_nl_cats = " ".join(
            c for c in cat_tags_list if c.startswith(("en:", "nl:"))
        )
        is_frozen = detect_is_frozen(
            title=selected_title,
            categories_tags=cat_tags_list,
            prop_icons=tags,
        )

        return {
            "barcode": clean_barcode,
            "name": clean_name,
            "brand": clean_brand,
            "category": map_category(en_or_nl_cats, "", clean_name),
            "preferred_store": infer_preferred_store_from_off(prod, raw_brand or clean_brand),
            "webshop_id": None,
            "package_size": prod.get("quantity"),
            "nutriscore": nutriscore,
            "is_vegan": is_vegan,
            "is_vegetarian": is_veg,
            "is_frozen": is_frozen,
            "nutrition": nutrition,
        }

    def search_product(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches Open Food Facts by keyword in Dutch/English."""
        clean_q = query.strip()
        if not clean_q:
            return None
        encoded = urllib.parse.quote(clean_q)
        url = f"{self.BASE_URL}/cgi/search.pl?search_terms={encoded}&search_simple=1&action=process&json=1&page_size=1"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "GroceryPi/2.0 (Raspberry Pi Touchscreen Kiosk)"},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                products = data.get("products") or []
                if products:
                    code = str(products[0].get("code") or "0000000000000")
                    return self.parse_off_product(code, products[0])
        except Exception as e:
            logger.debug(f"OpenFoodFacts search failed for '{clean_q}': {e}")
        return None

    def sync_cart(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Exports a portable checklist for general / Lidl items."""
        return {
            "store": "Lidl",
            "mode": "checklist_export",
            "synced_count": len(items),
            "checkout_url": None,
        }
