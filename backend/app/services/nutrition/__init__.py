"""
Package for the Nutrition Service.

Exports NutritionService and its shared instance (nutrition_service) to calculate
pantry nutrition totals for the Nutrition screen.
"""

from app.services.nutrition.nutrition import NutritionService, nutrition_service

__all__ = ["NutritionService", "nutrition_service"]
