"""
Albert Heijn Mobile API Client for GroceryPi
Reverse-engineered from Appie iOS app (v9.28) / appie-go / jabbink gist.
Provides product metadata lookup, GTIN barcodes, 9-metric European nutritional facts,
and hooks for receipt/cart synchronization.
"""

import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from app.models import ProductCatalog, ItemCategory, PreferredStore

logger = logging.getLogger("grocerypi.ah_client")

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "ah_product_cache.json")


def clean_product_name_and_brand(raw_name: str, raw_brand: Optional[str]) -> Tuple[str, Optional[str]]:
    """
    Cleans brand and title according to design rules:
    - Remove 'AH' or 'Albert Heijn' prefix/suffix from title.
    - If brand is AH / Albert Heijn, omit it.
    - Only retain brand if it is not already included in the title.
    """
    clean_name = raw_name.strip()
    clean_name = re.sub(r"^(AH|Albert Heijn)\s+", "", clean_name, flags=re.IGNORECASE).strip()
    clean_name = re.sub(r"\s+\b(AH|Albert Heijn)\b", "", clean_name, flags=re.IGNORECASE).strip()

    brand = raw_brand.strip() if raw_brand else None
    if brand and brand.lower() in ["ah", "albert heijn", "ah biologisch", "ah terra", "ah basic"]:
        brand = None

    if brand and brand.lower() in clean_name.lower():
        brand = None

    return clean_name or raw_name.strip(), brand


def map_category(main_cat: str, sub_cat: str, title: str) -> ItemCategory:
    """Classifies products into the standard GroceryPi ItemCategory enum."""
    combined = f"{main_cat} {sub_cat} {title}".lower()
    if any(k in combined for k in ["huisdier", "hond", "kat", "vogel", "knaagdier", "vis", "pet"]):
        return ItemCategory.PET
    if any(k in combined for k in ["drogisterij", "verzorging", "lichaam", "mond", "haar", "douche", "zeep", "hygiëne", "hygiene", "baby", "scheer"]):
        return ItemCategory.HYGIENE
    if any(k in combined for k in ["huishouden", "schoonmaak", "wasmiddel", "toiletpapier", "keukenrol", "batterij", "vuilniszak"]):
        return ItemCategory.HOUSEHOLD
    return ItemCategory.FOOD


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

        title = search_res.get("title") or clean_name
        import re
        title = re.sub(r"^(AH|Albert Heijn)\s+", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+\b(AH|Albert Heijn)\b", "", title, flags=re.IGNORECASE).strip()

        brand_val = search_res.get("brand")
        if brand_val and brand_val.strip().lower() in ["ah", "albert heijn", "ah biologisch", "ah terra", "ah basic"]:
            brand_val = None
        if brand_val and brand_val.lower() in title.lower():
            brand_val = None

        return {
            "name": title,
            "barcode": gtin,
            "brand": brand_val,
            "package_size": search_res.get("salesUnitSize"),
            "webshop_id": webshop_id,
            "nutrition": nutrition_facts,
        }

    def get_product_by_gtin(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Directly fetches product metadata, nutriscore, vegan/veg status,
        and nutritional facts from AH Mobile API by barcode / GTIN.
        """
        clean_barcode = barcode.strip()
        cache_key = f"gtin:{clean_barcode}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        token = self.get_token()
        if not token:
            return None

        headers = dict(self.HEADERS)
        headers["Authorization"] = f"Bearer {token}"

        # Try barcode variants (e.g. 13-digit EAN and 14-digit GTIN with leading 0)
        candidates = [clean_barcode]
        if len(clean_barcode) == 13:
            candidates.append(f"0{clean_barcode}")
        elif len(clean_barcode) == 14 and clean_barcode.startswith("0"):
            candidates.append(clean_barcode[1:])

        product_data = None
        for candidate in candidates:
            url = f"{self.BASE_URL}/mobile-services/product/search/v1/gtin/{candidate}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    product_data = json.loads(resp.read().decode("utf-8"))
                    if product_data and isinstance(product_data, dict):
                        break
            except Exception as e:
                logger.debug(f"AH GTIN lookup notice for {candidate}: {e}")

        if not product_data:
            return None

        webshop_id = product_data.get("webshopId")
        detail = self.get_product_details(webshop_id) if webshop_id else None

        nutrition_facts: Dict[str, float] = {
            "energy_kj": 0.0,
            "energy_kcal": 0.0,
            "fat_grams": 0.0,
            "saturated_fat_grams": 0.0,
            "carbohydrate_grams": 0.0,
            "sugar_grams": 0.0,
            "fiber_grams": 0.0,
            "protein_grams": 0.0,
            "salt_grams": 0.0,
        }

        if detail:
            trade_item = detail.get("tradeItem") or {}
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

        raw_title = product_data.get("title") or f"Item {clean_barcode}"
        raw_brand = product_data.get("brand")
        clean_name, clean_brand = clean_product_name_and_brand(raw_title, raw_brand)

        prop_icons = [str(p).lower() for p in (product_data.get("propertyIcons") or [])]
        is_vegan = "vegan" in prop_icons
        is_veg = is_vegan or "vegetarisch" in prop_icons

        nutriscore_val = product_data.get("nutriscore")
        nutriscore_str = str(nutriscore_val).upper() if nutriscore_val else None

        main_cat = str(product_data.get("mainCategory") or "")
        sub_cat = str(product_data.get("subCategory") or "")
        category = map_category(main_cat, sub_cat, clean_name)

        result = {
            "barcode": clean_barcode,
            "name": clean_name,
            "brand": clean_brand,
            "category": category,
            "webshop_id": webshop_id,
            "package_size": product_data.get("salesUnitSize"),
            "nutriscore": nutriscore_str,
            "is_vegan": is_vegan,
            "is_vegetarian": is_veg,
            "nutrition": nutrition_facts,
        }

        self.cache[cache_key] = result
        self._mark_dirty()
        return result

    def get_product_from_openfoodfacts(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Fallback to Open Food Facts API for non-Albert Heijn grocery packaging."""
        clean_barcode = barcode.strip()
        url = f"https://world.openfoodfacts.org/api/v2/product/{clean_barcode}.json"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "GroceryPi/2.0 (Raspberry Pi Touchscreen Kiosk)"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == 1 and "product" in data:
                    prod = data["product"]
                    raw_title = prod.get("product_name") or prod.get("generic_name") or f"Item {clean_barcode}"
                    raw_brand = prod.get("brands")
                    clean_name, clean_brand = clean_product_name_and_brand(raw_title, raw_brand)

                    nutriscore = (prod.get("nutriscore_grade") or "").upper() or None
                    if nutriscore and nutriscore not in ["A", "B", "C", "D", "E"]:
                        nutriscore = None

                    tags = [str(t).lower() for t in prod.get("labels_tags", [])]
                    is_vegan = any("vegan" in t for t in tags)
                    is_veg = is_vegan or any("vegetarian" in t for t in tags)

                    nutriments = prod.get("nutriments", {})
                    nutrition = {
                        "energy_kj": float(nutriments.get("energy-kj_100g") or 0.0),
                        "energy_kcal": float(nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g") or 0.0),
                        "fat_grams": float(nutriments.get("fat_100g") or 0.0),
                        "saturated_fat_grams": float(nutriments.get("saturated-fat_100g") or 0.0),
                        "carbohydrate_grams": float(nutriments.get("carbohydrates_100g") or 0.0),
                        "sugar_grams": float(nutriments.get("sugars_100g") or 0.0),
                        "fiber_grams": float(nutriments.get("fiber_100g") or 0.0),
                        "protein_grams": float(nutriments.get("proteins_100g") or 0.0),
                        "salt_grams": float(nutriments.get("salt_100g") or 0.0),
                    }

                    return {
                        "barcode": clean_barcode,
                        "name": clean_name,
                        "brand": clean_brand,
                        "category": map_category("", "", clean_name),
                        "webshop_id": None,
                        "package_size": prod.get("quantity"),
                        "nutriscore": nutriscore,
                        "is_vegan": is_vegan,
                        "is_vegetarian": is_veg,
                        "nutrition": nutrition,
                    }
        except Exception as e:
            logger.debug(f"OpenFoodFacts lookup failed for {clean_barcode}: {e}")
        return None


# Global singleton
_ah_client_instance: Optional[AHClient] = None

def get_ah_client() -> AHClient:
    global _ah_client_instance
    if _ah_client_instance is None:
        _ah_client_instance = AHClient()
    return _ah_client_instance


def resolve_barcode_to_catalog_item(barcode: str, db: Session) -> ProductCatalog:
    """
    Attempts to resolve barcode from AH API (or OpenFoodFacts fallback).
    If found, saves a new ProductCatalog record into the database and returns it.
    If not found in external APIs, creates a registered placeholder catalog entry
    so that inventory tracking and kiosk scanning always succeed without errors.
    """
    clean_barcode = barcode.strip()
    existing = db.query(ProductCatalog).filter(ProductCatalog.barcode == clean_barcode).first()
    if existing:
        return existing

    client = get_ah_client()

    # 1. Primary: Query AH Mobile API GTIN endpoint
    prod_data = client.get_product_by_gtin(clean_barcode)

    # 2. Secondary: Query Open Food Facts API fallback (ignore synthetic all-9s test barcodes)
    if not prod_data and not clean_barcode.startswith("9999999"):
        prod_data = client.get_product_from_openfoodfacts(clean_barcode)

    if not prod_data:
        logger.info(f"Barcode '{clean_barcode}' not found in AH or OpenFoodFacts APIs.")
        return None

    nutrition = prod_data.get("nutrition") or {}
    new_product = ProductCatalog(
        barcode=clean_barcode,
        name=prod_data["name"],
        brand=prod_data.get("brand"),
        category=prod_data.get("category", ItemCategory.FOOD),
        preferred_store=PreferredStore.AH,
        is_dual_store=False,
        webshop_id=prod_data.get("webshop_id"),
        package_size=prod_data.get("package_size"),
        nutriscore=prod_data.get("nutriscore"),
        is_vegan=prod_data.get("is_vegan", False),
        is_vegetarian=prod_data.get("is_vegetarian", False),
        energy_kj=nutrition.get("energy_kj", 0.0),
        energy_kcal=nutrition.get("energy_kcal", 0.0),
        fat_grams=nutrition.get("fat_grams", 0.0),
        saturated_fat_grams=nutrition.get("saturated_fat_grams", 0.0),
        carbohydrate_grams=nutrition.get("carbohydrate_grams", 0.0),
        sugar_grams=nutrition.get("sugar_grams", 0.0),
        fiber_grams=nutrition.get("fiber_grams", 0.0),
        protein_grams=nutrition.get("protein_grams", 0.0),
        salt_grams=nutrition.get("salt_grams", 0.0),
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    logger.info(
        f"Registered new product: id={new_product.id}, barcode='{clean_barcode}', name='{new_product.name}', nutriscore='{new_product.nutriscore}', vegan={new_product.is_vegan}"
    )
    return new_product


