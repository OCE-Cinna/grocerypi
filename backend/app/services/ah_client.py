"""
Albert Heijn Mobile API Client for GroceryPi
Reverse-engineered from Appie iOS app (v9.28) / appie-go / jabbink gist.
Provides product metadata lookup, GTIN barcodes, 9-metric European nutritional facts,
and hooks for receipt/cart synchronization.
"""

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("grocerypi.ah_client")

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "ah_product_cache.json")


class AHClient:
    BASE_URL = "https://api.ah.nl"
    AUTH_URL = "https://api.ah.nl/mobile-auth/v1/auth/token/anonymous"

    HEADERS = {
        "User-Agent": "Appie/9.28 (iPhone17,3; iPhone; CPU OS 26_1 like Mac OS X)",
        "x-client-name": "appie-ios",
        "x-client-version": "9.28",
        "x-application": "AHWEBSHOP",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.token: Optional[str] = None
        self.token_expiry: float = 0
        self.dirty_count: int = 0
        self.cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load AH cache: {e}")
        return {}

    def save_cache(self, force: bool = False):
        if not force and self.dirty_count < 50:
            return
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, self.cache_file)
            self.dirty_count = 0
        except Exception as e:
            logger.warning(f"Failed to save AH cache: {e}")

    def _mark_dirty(self):
        self.dirty_count += 1
        if self.dirty_count >= 50:
            self.save_cache(force=True)

    def get_token(self) -> Optional[str]:
        """Fetch or refresh anonymous auth token."""
        now = time.time()
        if self.token and now < (self.token_expiry - 60):
            return self.token

        try:
            req = urllib.request.Request(
                self.AUTH_URL,
                data=b'{"clientId": "appie-ios"}',
                headers=self.HEADERS,
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = now + expires_in
                return self.token
        except Exception as e:
            logger.error(f"Error fetching AH anonymous token: {e}")
            return None

    def search_product(self, query: str) -> Optional[Dict[str, Any]]:
        """Search AH catalog for the best matching product."""
        clean_q = query.strip()
        cache_key = f"search:{clean_q.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        token = self.get_token()
        if not token:
            return None

        headers = dict(self.HEADERS)
        headers["Authorization"] = f"Bearer {token}"

        encoded_q = urllib.parse.quote(clean_q)
        url = f"{self.BASE_URL}/mobile-services/product/search/v2?query={encoded_q}&page=0&size=1&sortOn=RELEVANCE"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                products = data.get("products", [])
                if products:
                    match = products[0]
                    self.cache[cache_key] = match
                    self._mark_dirty()
                    return match
        except Exception as e:
            logger.warning(f"AH search failed for '{query}': {e}")

        return None

    def get_product_details(self, webshop_id: int) -> Optional[Dict[str, Any]]:
        """Get product full details (GTIN, nutritional information, etc.)."""
        cache_key = f"detail:{webshop_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        token = self.get_token()
        if not token:
            return None

        headers = dict(self.HEADERS)
        headers["Authorization"] = f"Bearer {token}"
        url = f"{self.BASE_URL}/mobile-services/product/detail/v4/fir/{webshop_id}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.cache[cache_key] = data
                self._mark_dirty()
                return data
        except Exception as e:
            logger.warning(f"AH detail failed for webshop_id {webshop_id}: {e}")

        return None

    def resolve_product(self, raw_name: str) -> Dict[str, Any]:
        """
        Takes a raw name from a receipt/invoice and resolves official product title,
        GTIN barcode, brand, package size, and European nutritional facts.
        """
        # Clean marketing tags from raw receipt name
        clean_name = raw_name
        for tag in [" BONUS", " voordeel", " stapelkorting", " 1+1 gratis", " 2e halve prijs"]:
            clean_name = clean_name.replace(tag, "").replace(tag.lower(), "")
        clean_name = clean_name.strip()

        search_res = self.search_product(clean_name)
        if not search_res:
            # Fallback to search by first 3 words if multi-word
            words = clean_name.split()
            if len(words) > 3:
                search_res = self.search_product(" ".join(words[:3]))

        if not search_res:
            return {
                "name": clean_name,
                "barcode": None,
                "brand": None,
                "package_size": None,
                "webshop_id": None,
                "nutrition": {},
            }

        webshop_id = search_res.get("webshopId")
        detail = self.get_product_details(webshop_id) if webshop_id else None

        gtin = None
        nutrition_facts: Dict[str, float] = {}

        if detail:
            trade_item = detail.get("tradeItem") or {}
            gtin = trade_item.get("gtin")
            # If GTIN has a leading zero, e.g. 0871..., make it clean 13-digit EAN if length is 14
            if gtin and len(gtin) == 14 and gtin.startswith("0"):
                gtin = gtin[1:]

            nutri_info = trade_item.get("nutritionalInformation") or {}
            headers_list = nutri_info.get("nutrientHeaders") or []
            if headers_list:
                details = headers_list[0].get("nutrientDetail") or []
                for d in details:
                    code = (d.get("nutrientTypeCode") or {}).get("value")
                    qty_contained = d.get("quantityContained") or []
                    if qty_contained and code:
                        val = qty_contained[0].get("value")
                        unit = (qty_contained[0].get("measurementUnitCode") or {}).get("value")
                        if val is not None:
                            try:
                                fval = float(val)
                                if code == "ENER-" and unit == "kJ":
                                    nutrition_facts["energy_kj"] = fval
                                elif code == "ENER-" and unit == "kcal":
                                    nutrition_facts["energy_kcal"] = fval
                                elif code == "FAT":
                                    nutrition_facts["fat_grams"] = fval
                                elif code == "FASAT":
                                    nutrition_facts["saturated_fat_grams"] = fval
                                elif code == "CHOAVL":
                                    nutrition_facts["carbohydrate_grams"] = fval
                                elif code == "SUGAR-":
                                    nutrition_facts["sugar_grams"] = fval
                                elif code == "FIBTG":
                                    nutrition_facts["fiber_grams"] = fval
                                elif code == "PRO-":
                                    nutrition_facts["protein_grams"] = fval
                                elif code == "SALTEQ":
                                    nutrition_facts["salt_grams"] = fval
                            except ValueError:
                                pass

        return {
            "name": search_res.get("title") or clean_name,
            "barcode": gtin,
            "brand": search_res.get("brand"),
            "package_size": search_res.get("salesUnitSize"),
            "webshop_id": webshop_id,
            "nutrition": nutrition_facts,
        }

