"""Catalog loader - loads catalog definitions from YAML/JSON files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .registry import CatalogRegistry
from .types import CatalogNode, Ownership, SourceBinding, SourceType


logger = logging.getLogger(__name__)


class CatalogLoader:
    """
    Loads catalog definitions from YAML or JSON files.

    File format:
    ```yaml
    market-data:
      display_name: Market Data
      description: Real-time and historical market data
      ownership:
        accountable_owner: jane@firm.com
        data_specialist: team@firm.com
        support_channel: "#market-data"

    market-data/prices/equity:
      display_name: Equity Prices
      source_binding:
        type: snowflake
        config:
          account: acme.us-east-1
          database: MARKET_DATA
          query: "SELECT * FROM PRICES WHERE symbol = '{path}'"
    ```
    """

    def load_file(self, path: str | Path) -> CatalogRegistry:
        """Load catalog from a YAML or JSON file."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Catalog file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                import json
                data = json.load(f)

        return self.load_dict(data or {})

    def load_dict(self, data: dict[str, Any]) -> CatalogRegistry:
        """Load catalog from a dictionary."""
        registry = CatalogRegistry()

        for path, node_data in data.items():
            node = self._parse_node(path, node_data)
            registry.register(node)
            logger.debug(f"Loaded catalog node: {path}")

        logger.info(f"Loaded {len(registry.all_paths())} catalog nodes")
        return registry

    def _parse_node(self, path: str, data: dict[str, Any]) -> CatalogNode:
        """Parse a single catalog node from dictionary."""
        # Parse ownership
        ownership = Ownership()
        if "ownership" in data:
            own_data = data["ownership"]
            ownership = Ownership(
                accountable_owner=own_data.get("accountable_owner"),
                data_specialist=own_data.get("data_specialist"),
                support_channel=own_data.get("support_channel"),
            )

        # Parse source binding
        source_binding = None
        if "source_binding" in data:
            sb_data = data["source_binding"]
            source_type_str = sb_data.get("type", "").lower()

            try:
                source_type = SourceType(source_type_str)
            except ValueError:
                logger.warning(f"Unknown source type '{source_type_str}' for {path}")
                source_type = SourceType.STATIC

            source_binding = SourceBinding(
                source_type=source_type,
                config=sb_data.get("config", {}),
                schema=sb_data.get("schema"),
                read_only=sb_data.get("read_only", True),
            )

        # Parse tags
        tags = frozenset(data.get("tags", []))

        return CatalogNode(
            path=path,
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            ownership=ownership,
            source_binding=source_binding,
            classification=data.get("classification", "internal"),
            tags=tags,
            metadata=data.get("metadata", {}),
            is_leaf=source_binding is not None,
        )

    def load_directory(self, directory: str | Path) -> CatalogRegistry:
        """
        Load catalog from all YAML/JSON files in a directory.

        Files are loaded in alphabetical order. Later files can override
        earlier definitions.
        """
        directory = Path(directory)
        registry = CatalogRegistry()

        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        files = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml")) + sorted(directory.glob("*.json"))

        for file_path in files:
            logger.info(f"Loading catalog file: {file_path}")
            file_registry = self.load_file(file_path)
            for node in file_registry.all_nodes():
                registry.register(node)

        return registry


def load_catalog(source: str | Path | dict) -> CatalogRegistry:
    """
    Convenience function to load a catalog.

    Args:
        source: File path, directory path, or dictionary

    Returns:
        CatalogRegistry with loaded nodes
    """
    loader = CatalogLoader()

    if isinstance(source, dict):
        return loader.load_dict(source)

    path = Path(source)
    if path.is_dir():
        return loader.load_directory(path)
    else:
        return loader.load_file(path)
