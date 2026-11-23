"""
Nutrition calculation service for GroceryPi.

This file looks at all food items currently stocked in the kitchen and adds up
their nutrition values (calories, protein, carbohydrates, sugar, fat, fiber,
and salt). It also calculates the average Nutri-Score grade (A to E) and counts
how many vegan and vegetarian items are in the pantry.
"""

from typing import Any, Dict
from sqlalchemy.orm import Session

from app.db.repositories.inventory_repository import InventoryRepository


class NutritionService:
    """Calculates total nutrition and diet summaries across all stocked kitchen items."""

    # Converts letter grades (A to E) into numbers (1 to 5) so we can calculate an average
    NUTRISCORE_MAP = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
    REVERSE_NUTRISCORE_MAP = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}

    def __init__(self, inventory_repo: type[InventoryRepository] = InventoryRepository):
        """Connects the nutrition calculator to the inventory database helper."""
        self.inventory_repo = inventory_repo

    def get_pantry_summary(self, db: Session) -> Dict[str, Any]:
        """
        Loops through every item currently in stock, multiplies its nutrition
        values by the number of units owned, and returns the combined totals
        for the Nutritional Insights screen.
        """
        items = self.inventory_repo.list_stocked_with_products(db)

        summary: Dict[str, Any] = {
            "total_items_counted": 0,
            "total_energy_kj": 0.0,
            "total_energy_kcal": 0.0,
            "total_fat_grams": 0.0,
            "total_saturated_fat_grams": 0.0,
            "total_carbohydrate_grams": 0.0,
            "total_sugar_grams": 0.0,
            "total_fiber_grams": 0.0,
            "total_protein_grams": 0.0,
            "total_salt_grams": 0.0,
        }

        nutriscore_weighted_sum = 0
        nutriscore_total_units = 0
        nutriscore_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
        total_vegetarian = 0
        total_vegan = 0

        for item in items:
            p = item.product
            if not p:
                continue
            qty = item.quantity
            summary["total_items_counted"] += qty
            summary["total_energy_kj"] += p.energy_kj * qty
            summary["total_energy_kcal"] += p.energy_kcal * qty
            summary["total_fat_grams"] += p.fat_grams * qty
            summary["total_saturated_fat_grams"] += p.saturated_fat_grams * qty
            summary["total_carbohydrate_grams"] += p.carbohydrate_grams * qty
            summary["total_sugar_grams"] += p.sugar_grams * qty
            summary["total_fiber_grams"] += p.fiber_grams * qty
            summary["total_protein_grams"] += p.protein_grams * qty
            summary["total_salt_grams"] += p.salt_grams * qty

            # Count vegan and vegetarian items separately so no item is counted twice
            if p.is_vegan:
                total_vegan += qty
            elif p.is_vegetarian:
                total_vegetarian += qty

            if p.nutriscore and p.nutriscore.upper() in self.NUTRISCORE_MAP:
                ns = p.nutriscore.upper()
                nutriscore_counts[ns] += qty
                nutriscore_weighted_sum += self.NUTRISCORE_MAP[ns] * qty
                nutriscore_total_units += qty

        # Round all decimal nutrition totals to 2 decimal places
        for k in list(summary.keys()):
            if isinstance(summary[k], float):
                summary[k] = round(summary[k], 2)

        avg_numeric = (
            round(nutriscore_weighted_sum / nutriscore_total_units, 2)
            if nutriscore_total_units > 0
            else None
        )
        avg_letter = None
        if avg_numeric is not None:
            rounded_val = min(5, max(1, round(avg_numeric)))
            avg_letter = self.REVERSE_NUTRISCORE_MAP.get(rounded_val, "B")

        summary["average_nutriscore"] = avg_letter
        summary["average_nutriscore_numeric"] = avg_numeric
        summary["total_vegetarian_items"] = total_vegetarian
        summary["total_vegan_items"] = total_vegan
        summary["nutriscore_counts"] = nutriscore_counts

        return summary


# Shared instance used by the inventory router
nutrition_service = NutritionService()
