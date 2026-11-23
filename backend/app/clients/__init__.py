"""
Package for external supermarket API connections.

Exports the common IStoreGateway template that store clients follow.
"""

from app.clients.store_gateway import IStoreGateway

__all__ = ["IStoreGateway"]
