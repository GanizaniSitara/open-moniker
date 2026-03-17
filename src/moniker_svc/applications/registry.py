"""
Thread-safe application registry.

Provides centralized storage and access to application configurations,
including reverse lookups by dataset and field patterns.
"""

import fnmatch
import threading
from typing import Dict, List, Optional

from .types import Application


class ApplicationRegistry:
    """
    Thread-safe registry for application configurations.

    Provides methods to register, retrieve, and manage applications,
    including reverse lookups to find which applications use a given
    dataset or field.
    """

    def __init__(self):
        self._applications: Dict[str, Application] = {}
        self._lock = threading.RLock()

    def register(self, application: Application) -> None:
        """Register an application in the registry."""
        with self._lock:
            if application.key in self._applications:
                raise ValueError(f"Application '{application.key}' already registered")
            self._applications[application.key] = application

    def register_or_update(self, application: Application) -> None:
        """Register an application, or update if it already exists."""
        with self._lock:
            self._applications[application.key] = application

    def get(self, key: str) -> Optional[Application]:
        """Get an application by key."""
        with self._lock:
            return self._applications.get(key)

    def get_or_raise(self, key: str) -> Application:
        """Get an application by key, raising if not found."""
        with self._lock:
            if key not in self._applications:
                raise KeyError(f"Application '{key}' not found")
            return self._applications[key]

    def exists(self, key: str) -> bool:
        """Check if an application exists."""
        with self._lock:
            return key in self._applications

    def all_applications(self) -> List[Application]:
        """Get all registered applications, sorted by key."""
        with self._lock:
            return sorted(self._applications.values(), key=lambda a: a.key)

    def application_keys(self) -> List[str]:
        """Get all registered application keys."""
        with self._lock:
            return sorted(self._applications.keys())

    def delete(self, key: str) -> bool:
        """Delete an application from the registry."""
        with self._lock:
            if key in self._applications:
                del self._applications[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all applications from the registry."""
        with self._lock:
            self._applications.clear()

    def count(self) -> int:
        """Get the number of registered applications."""
        with self._lock:
            return len(self._applications)

    def find_by_dataset(self, dataset_path: str) -> List[Application]:
        """
        Find applications that reference a given dataset path.

        Uses fnmatch glob matching against each application's dataset patterns.
        The dataset_path is matched with both dot and slash separators.

        Args:
            dataset_path: A dataset path like "prices.equity.us/daily"

        Returns:
            List of applications whose dataset patterns match
        """
        with self._lock:
            matches = []
            for app in self._applications.values():
                for pattern in app.datasets:
                    if fnmatch.fnmatch(dataset_path, pattern):
                        matches.append(app)
                        break
            return sorted(matches, key=lambda a: a.key)

    def find_by_field(self, field_path: str) -> List[Application]:
        """
        Find applications that reference a given field/model path.

        Uses exact matching against each application's field list.

        Args:
            field_path: A model path like "risk.analytics/dv01"

        Returns:
            List of applications whose fields list contains the path
        """
        with self._lock:
            matches = []
            for app in self._applications.values():
                if field_path in app.fields:
                    matches.append(app)
                    break  # already matched
            return sorted(matches, key=lambda a: a.key)

    def __len__(self) -> int:
        return self.count()

    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    def __iter__(self):
        return iter(self.all_applications())
