#!/usr/bin/env python3
"""Generate test JWT tokens for local development.

Usage:
    python scripts/generate_test_token.py --secret "your-secret" --user "testuser"
    python scripts/generate_test_token.py --secret "your-secret" --user "testuser" --expires 3600

The generated token can be used with the moniker client:
    export MONIKER_AUTH_METHOD=jwt
    export MONIKER_JWT=<generated-token>
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta

try:
    from jose import jwt
except ImportError:
    print("Error: python-jose not installed. Run: pip install python-jose[cryptography]")
    sys.exit(1)


def generate_test_token(
    secret: str,
    user: str,
    expires_in: int = 3600,
    audience: str | None = None,
    groups: list[str] | None = None,
) -> str:
    """
    Generate a test JWT token for local development.

    Args:
        secret: Shared secret for HS256 signing (must match server's test_secret)
        user: Username to embed in the token (sub claim)
        expires_in: Token lifetime in seconds (default: 1 hour)
        audience: Optional audience claim
        groups: Optional list of groups

    Returns:
        Signed JWT token string
    """
    now = datetime.now(timezone.utc)

    claims = {
        "iss": "test",
        "sub": user,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }

    if audience:
        claims["aud"] = audience

    if groups:
        claims["groups"] = groups

    return jwt.encode(claims, secret, algorithm="HS256")


def main():
    parser = argparse.ArgumentParser(
        description="Generate test JWT tokens for local development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a basic token
  python scripts/generate_test_token.py --secret "my-test-secret-at-least-32-chars" --user "alice"

  # Token with audience and groups
  python scripts/generate_test_token.py --secret "my-test-secret" --user "alice" \\
      --audience "api://moniker-svc" --groups "data-team" "admins"

  # Long-lived token (24 hours)
  python scripts/generate_test_token.py --secret "my-test-secret" --user "alice" --expires 86400

Server config (config.yaml):
  auth:
    enabled: true
    okta:
      enabled: true
      issuer: "test"
      test_secret: "my-test-secret-at-least-32-chars"

Client usage:
  export MONIKER_AUTH_METHOD=jwt
  export MONIKER_JWT=<generated-token>
        """,
    )

    parser.add_argument(
        "--secret",
        required=True,
        help="Shared secret for signing (must match server's test_secret)",
    )
    parser.add_argument(
        "--user",
        required=True,
        help="Username to embed in token (sub claim)",
    )
    parser.add_argument(
        "--expires",
        type=int,
        default=3600,
        help="Token lifetime in seconds (default: 3600 = 1 hour)",
    )
    parser.add_argument(
        "--audience",
        help="Audience claim (optional, must match server's audience if set)",
    )
    parser.add_argument(
        "--groups",
        nargs="*",
        help="Groups to include in token (optional)",
    )

    args = parser.parse_args()

    if len(args.secret) < 32:
        print("Warning: Secret should be at least 32 characters for security")

    token = generate_test_token(
        secret=args.secret,
        user=args.user,
        expires_in=args.expires,
        audience=args.audience,
        groups=args.groups,
    )

    print(f"\n# Token for user '{args.user}' (expires in {args.expires}s):")
    print(f"export MONIKER_JWT={token}\n")

    # Also decode and show claims for verification
    claims = jwt.decode(token, args.secret, algorithms=["HS256"], options={"verify_aud": False})
    print("# Token claims:")
    for key, value in claims.items():
        if key in ("iat", "exp"):
            value = datetime.fromtimestamp(value, timezone.utc).isoformat()
        print(f"#   {key}: {value}")


if __name__ == "__main__":
    main()
