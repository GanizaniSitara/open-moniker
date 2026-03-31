"""
Application Configuration Layer

Provides application-level metadata for tracking which business applications
consume or produce datasets and fields in the moniker catalog.
"""

from .types import Application
from .registry import ApplicationRegistry
from .loader import load_applications_from_yaml
from .serializer import save_applications_to_yaml

__all__ = [
    "Application",
    "ApplicationRegistry",
    "load_applications_from_yaml",
    "save_applications_to_yaml",
]
