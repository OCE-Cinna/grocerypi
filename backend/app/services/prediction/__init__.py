"""
Package for the Replenishment Prediction Service.

Exports PredictionEngine, its shared instance (prediction_engine), and the
helper function used to build suggested supermarket shopping lists.
"""

from app.services.prediction.prediction import (
    PredictionEngine,
    get_cart_replenishment_suggestions,
    prediction_engine,
)

__all__ = [
    "PredictionEngine",
    "prediction_engine",
    "get_cart_replenishment_suggestions",
]
