#!/usr/bin/env python3
"""
Automated Render.com Deployment Script

Uses Render API to deploy services programmatically.
"""
import json
import os
import sys
import time
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

def api_request(method, endpoint, data=None):
    """Make API request to Render."""
    url = f"{RENDER_API_BASE}{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    
    if response.status_code >= 400:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return None
    
    return response.json() if response.text else {}

def create_postgres_database():
    """Create PostgreSQL database for telemetry."""
    print("\n📊 Creating PostgreSQL database...")
    
    data = {
        "name": "moniker-telemetry",
        "databaseName": "moniker_telemetry",
        "databaseUser": "moniker",
        "region": "oregon",
        "plan": "starter",
        "ipAllowList": []
    }
    
    result = api_request("POST", "/postgres", data)
    if result:
        print(f"✅ Database created: {result.get('id')}")
        return result
    return None

def create_python_service(db_id):
    """Create Python admin service."""
    print("\n🐍 Creating Python admin service...")

    data = {
        "name": "moniker-admin",
        "type": "web_service",
        "repo": GITHUB_REPO,
        "branch": BRANCH,
        "region": "oregon",
        "plan": "free",
        "runtime": "python",
        "envSpecificDetails": {
            "buildCommand": "pip install --upgrade pip && pip install -r requirements.txt",
            "startCommand": "cd src && PYTHONPATH=/opt/render/project/src uvicorn moniker_svc.management_app:app --host 0.0.0.0 --port $PORT",
            "healthCheckPath": "/health",
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
    
    result = api_request("POST", "/services", data)
    if result:
        print(f"✅ Python service created: {result.get('service', {}).get('id')}")
        return result
    return None

def create_java_service():
    """Create Java resolver service."""
    print("\n☕ Creating Java resolver service...")

    data = {
        "name": "moniker-resolver-java",
        "type": "web_service",
        "repo": GITHUB_REPO,
        "branch": BRANCH,
        "region": "oregon",
        "plan": "free",
        "runtime": "docker",
        "dockerfilePath": "./deployments/render/Dockerfile.java",
        "dockerContext": ".",
        "healthCheckPath": "/health",
        "envVars": [
            {"key": "SERVER_PORT", "value": "8054"},
            {"key": "CONFIG_FILE", "value": "/app/sample_config.yaml"},
            {"key": "CATALOG_FILE", "value": "/app/sample_catalog.yaml"},
            {"key": "MONIKER_TELEMETRY_ENABLED", "value": "true"},
            {"key": "RESOLVER_NAME", "value": "render-java-1"},
            {"key": "AWS_REGION", "value": "us-west-2"},
            {"key": "AWS_AZ", "value": "render"},
            {"key": "TELEMETRY_SINK_TYPE", "value": "postgres"},
            {"key": "TELEMETRY_DB_HOST", "fromDatabase": {"name": "moniker-telemetry", "property": "host"}},
            {"key": "TELEMETRY_DB_PORT", "fromDatabase": {"name": "moniker-telemetry", "property": "port"}},
            {"key": "TELEMETRY_DB_NAME", "fromDatabase": {"name": "moniker-telemetry", "property": "database"}},
            {"key": "TELEMETRY_DB_USER", "fromDatabase": {"name": "moniker-telemetry", "property": "user"}},
            {"key": "TELEMETRY_DB_PASSWORD", "fromDatabase": {"name": "moniker-telemetry", "property": "password"}},
        ]
    }
    
    result = api_request("POST", "/services", data)
    if result:
        print(f"✅ Java service created: {result.get('service', {}).get('id')}")
        return result
    return None

def list_services():
    """List all services."""
    print("\n📋 Listing existing services...")
    result = api_request("GET", "/services")
    if result:
        for service in result:
            svc = service.get("service", {})
            print(f"  - {svc.get('name')}: {svc.get('serviceDetails', {}).get('url')}")
    return result

def main():
    print("=" * 60)
    print("RENDER.COM AUTOMATED DEPLOYMENT")
    print("=" * 60)
    
    # List existing services first
    existing = list_services()
    
    # Check if services already exist
    if existing:
        print("\n⚠️  Services already exist. Delete them first or use existing ones.")
        sys.exit(0)
    
    # Create database
    db = create_postgres_database()
    if not db:
        print("❌ Failed to create database")
        sys.exit(1)
    
    time.sleep(2)
    
    # Create Python service
    python_svc = create_python_service(db.get("id"))
    if not python_svc:
        print("❌ Failed to create Python service")
        sys.exit(1)
    
    time.sleep(2)
    
    # Create Java service
    java_svc = create_java_service()
    if not java_svc:
        print("❌ Failed to create Java service")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ DEPLOYMENT INITIATED!")
    print("=" * 60)
    print("\nServices are building now. This will take 5-10 minutes.")
    print("Check status at: https://dashboard.render.com/")
    print("\nRun test_render.py once services are live to verify.")

if __name__ == "__main__":
    main()
