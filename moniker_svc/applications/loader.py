"""
Application configuration loader.

Load applications from YAML files.
"""

from pathlib import Path
from typing import List, Optional

import yaml

from .types import Application
from .registry import ApplicationRegistry


def load_applications_from_yaml(
    file_path: str | Path,
    registry: Optional[ApplicationRegistry] = None
) -> List[Application]:
    """
    Load applications from a YAML file.

    Expected format:
        murex:
          display_name: Murex
          description: Cross-asset trading and risk management platform
          category: Trading
          color: "#8E44AD"
          ...

    Args:
        file_path: Path to the YAML file
        registry: Optional registry to populate

    Returns:
        List of loaded applications
    """
    path = Path(file_path)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    applications = []
    for key, config in data.items():
        if isinstance(config, dict):
            application = Application.from_dict(key, config)
            applications.append(application)
            if registry is not None:
                registry.register_or_update(application)

    return applications
