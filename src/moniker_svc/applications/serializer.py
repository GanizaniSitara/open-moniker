"""
Application configuration serializer.

Save applications to YAML format.
"""

import os
from pathlib import Path
from typing import List, Union

import yaml

from .types import Application
from .registry import ApplicationRegistry


def save_applications_to_yaml(
    applications: Union[List[Application], ApplicationRegistry],
    file_path: str | Path
) -> None:
    """
    Save applications to a YAML file.

    Args:
        applications: List of applications or an ApplicationRegistry
        file_path: Path to write the YAML file
    """
    if isinstance(applications, ApplicationRegistry):
        app_list = applications.all_applications()
    else:
        app_list = sorted(applications, key=lambda a: a.key)

    data = {}
    for app in app_list:
        app_data = {
            "display_name": app.display_name,
            "description": app.description,
            "category": app.category,
            "color": app.color,
            "status": app.status,
            "owner": app.owner,
            "tech_lead": app.tech_lead,
            "support_channel": app.support_channel,
            "datasets": app.datasets,
            "fields": app.fields,
            "documentation_url": app.documentation_url,
            "wiki_link": app.wiki_link,
        }
        # Remove empty string values and empty lists for cleaner output
        app_data = {
            k: v for k, v in app_data.items()
            if v is not None and (v or isinstance(v, bool))
        }
        data[app.key] = app_data

    path = Path(file_path).resolve()
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Business Applications Configuration\n")
        f.write("# Tracks which applications consume or produce datasets and fields\n\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        f.flush()
        os.fsync(f.fileno())
