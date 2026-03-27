#!/usr/bin/env python
"""Start the Moniker Service.

Usage:
    python start.py              # Default: prod on port 8060
    python start.py --env prod   # Prod on port 8060
    python start.py --env dev    # Dev on port 8061
    python start.py --host 0.0.0.0:9000  # Custom host:port
"""

import argparse
import os
from pathlib import Path

# Change to script directory so relative paths work correctly
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

# Environment configurations
ENV_CONFIG = {
    "prod": {"host": "0.0.0.0", "port": 8060},
    "dev": {"host": "0.0.0.0", "port": 8061},
}


def parse_host(host_str: str) -> tuple[str, int]:
    """Parse host:port string."""
    if ":" in host_str:
        host, port_str = host_str.rsplit(":", 1)
        return host, int(port_str)
    else:
        # Just a host, use default port
        return host_str, 8060


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the Moniker Service")
    parser.add_argument(
        "--env", "-e",
        choices=["prod", "dev"],
        default="prod",
        help="Environment: prod (port 8060) or dev (port 8061). Default: prod"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Custom host:port (e.g., 0.0.0.0:9000). Overrides --env setting."
    )
    args = parser.parse_args()

    # Determine host and port
    if args.host:
        host, port = parse_host(args.host)
    else:
        config = ENV_CONFIG[args.env]
        host, port = config["host"], config["port"]

    print(f"Starting Moniker Service ({args.env}) on {host}:{port}")

    import uvicorn
    uvicorn.run("moniker_svc.main:app", host=host, port=port, reload=False)
