#!/usr/bin/env python3
"""
Create Python Admin Service on Render.com

Quick script to create just the Python service since DB and Java already exist.
"""
import json
import requests
from pathlib import Path

# Configuration
RENDER_API_KEY = open(Path.home() / ".render_api_key").read().strip()
RENDER_API_BASE = "https://api.render.com/v1"
GITHUB_REPO = "https://github.com/MSubhan6/open-moniker.git"
BRANCH = "feature/java-resolver-implementation"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json"
}

def create_python_service():
    """Create Python admin service."""
    print("\n🐍 Creating Python admin service...")

    data = {
        "name": "moniker-admin",
        "ownerId": "tea-d5rjn7h5pdvs739q52rg",
        "type": "web_service",
        "repo": GITHUB_REPO,
        "branch": BRANCH,
        "serviceDetails": {
            "env": "python",
            "region": "oregon",
            "plan": "starter",
            "runtime": "python",
            "healthCheckPath": "/health",
            "envSpecificDetails": {
                "buildCommand": "pip install --upgrade pip && pip install -r requirements.txt",
                "startCommand": "cd src && PYTHONPATH=/opt/render/project/src uvicorn moniker_svc.management_app:app --host 0.0.0.0 --port $PORT",
            },
            "envVars": [
                {"key": "PYTHONPATH", "value": "/opt/render/project/src"},
                {"key": "CONFIG_FILE", "value": "/opt/render/project/src/sample_config.yaml"},
                {"key": "CATALOG_FILE", "value": "/opt/render/project/src/sample_catalog.yaml"},
                {"key": "TELEMETRY_DB_TYPE", "value": "postgres"},
                {"key": "PROJECT_NAME", "value": "Open Moniker (Render)"},
                {"key": "TELEMETRY_DB_HOST", "fromDatabase": {"name": "moniker-telemetry", "property": "host"}},
                {"key": "TELEMETRY_DB_PORT", "fromDatabase": {"name": "moniker-telemetry", "property": "port"}},
                {"key": "TELEMETRY_DB_NAME", "fromDatabase": {"name": "moniker-telemetry", "property": "database"}},
                {"key": "TELEMETRY_DB_USER", "fromDatabase": {"name": "moniker-telemetry", "property": "user"}},
                {"key": "TELEMETRY_DB_PASSWORD", "fromDatabase": {"name": "moniker-telemetry", "property": "password"}},
            ]
        }
    }

    url = f"{RENDER_API_BASE}/services"
    print(f"📡 POST {url}")
    print(f"📦 Payload: {json.dumps(data, indent=2)}")

    response = requests.post(url, headers=headers, json=data)

    print(f"\n📊 Status: {response.status_code}")

    if response.status_code >= 400:
        print(f"❌ Failed: {response.text}")
        return None

    result = response.json() if response.text else {}
    print(f"✅ Success!")
    print(f"📄 Response: {json.dumps(result, indent=2)}")

    # Save URL
    service_url = result.get('service', {}).get('serviceDetails', {}).get('url', 'N/A')
    print(f"\n🌐 Service URL: {service_url}")

    with open("/tmp/python_service_url.txt", "w") as f:
        f.write(service_url + "\n")

    return result

if __name__ == "__main__":
    print("=" * 60)
    print("RENDER.COM - CREATE PYTHON SERVICE")
    print("=" * 60)
    create_python_service()
