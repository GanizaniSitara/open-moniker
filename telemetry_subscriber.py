#!/usr/bin/env python3
"""
ZeroMQ Telemetry Subscriber Demo

This script subscribes to the moniker service telemetry stream and prints
events as they arrive. Use this as a starting point for building your own
telemetry consumers (e.g., to push to Kafka, Splunk, or a data warehouse).

Usage:
    # Terminal 1: Start the service with ZMQ telemetry
    MONIKER_TELEMETRY_SINK=zmq python -m moniker_svc.main

    # Terminal 2: Run this subscriber
    python telemetry_subscriber.py

Requirements:
    pip install pyzmq
"""

import argparse
import json
import signal
import sys
from datetime import datetime

try:
    import zmq
except ImportError:
    print("Error: pyzmq not installed. Run: pip install pyzmq")
    sys.exit(1)


def format_event(event: dict, verbose: bool = False) -> str:
    """Format a telemetry event for display."""
    ts = event.get("timestamp", "")
    if ts:
        # Parse and format timestamp
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts = dt.strftime("%H:%M:%S.%f")[:-3]
        except (ValueError, AttributeError):
            pass

    op = event.get("operation", "?")
    outcome = event.get("outcome", "?")
    moniker = event.get("moniker_path", event.get("moniker", "?"))
    caller = event.get("caller", {})
    principal = caller.get("principal", "anonymous")
    latency = event.get("latency_ms")

    # Color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    # Outcome color
    if outcome == "success":
        outcome_color = GREEN
    elif outcome == "error":
        outcome_color = RED
    else:
        outcome_color = YELLOW

    latency_str = f" ({latency:.1f}ms)" if latency else ""

    line = f"{CYAN}[{ts}]{RESET} {op.upper():8} {outcome_color}{outcome:10}{RESET} {moniker} <- {principal}{latency_str}"

    if verbose:
        # Add extra details
        source_type = event.get("source_type", "")
        if source_type:
            line += f" [{source_type}]"
        row_count = event.get("row_count")
        if row_count is not None:
            line += f" rows={row_count}"

    return line


def main():
    parser = argparse.ArgumentParser(
        description="Subscribe to moniker service telemetry stream"
    )
    parser.add_argument(
        "--endpoint",
        default="tcp://localhost:5556",
        help="ZeroMQ endpoint to connect to (default: tcp://localhost:5556)",
    )
    parser.add_argument(
        "--topic",
        default="",
        help="Topic filter (default: all topics)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw JSON instead of formatted output",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show additional event details",
    )
    parser.add_argument(
        "--stats-interval",
        type=int,
        default=0,
        help="Print stats every N events (0 = disabled)",
    )
    args = parser.parse_args()

    # Set up signal handler for clean exit
    def signal_handler(sig, frame):
        print("\nShutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Connect to ZeroMQ
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    print(f"Connecting to {args.endpoint}...")
    socket.connect(args.endpoint)

    # Subscribe to topic (empty string = all topics)
    socket.setsockopt_string(zmq.SUBSCRIBE, args.topic)

    if args.topic:
        print(f"Subscribed to topic: {args.topic}")
    else:
        print("Subscribed to all topics")

    print("Waiting for telemetry events...\n")
    print("-" * 80)

    event_count = 0
    error_count = 0

    while True:
        try:
            # Receive message (may have topic prefix)
            message = socket.recv_string()

            # Parse JSON (handle topic prefix if present)
            if message.startswith("{"):
                data = json.loads(message)
            else:
                # Topic prefix: "topic {json}"
                parts = message.split(" ", 1)
                if len(parts) == 2:
                    data = json.loads(parts[1])
                else:
                    data = {"raw": message}

            event_count += 1

            if args.raw:
                print(json.dumps(data, indent=2))
            else:
                print(format_event(data, verbose=args.verbose))

            # Stats
            if args.stats_interval > 0 and event_count % args.stats_interval == 0:
                print(f"\n--- {event_count} events received, {error_count} errors ---\n")

        except json.JSONDecodeError as e:
            error_count += 1
            print(f"JSON decode error: {e}")
        except zmq.ZMQError as e:
            error_count += 1
            print(f"ZMQ error: {e}")
            break


if __name__ == "__main__":
    main()
