"""FastAPI dependency injection functions for authentication."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ..telemetry.events import CallerIdentity
from .authenticator import AuthResult, CompositeAuthenticator

logger = logging.getLogger(__name__)

# Global authenticator instance (set by main.py during startup)
_authenticator: CompositeAuthenticator | None = None

# Cached singletons for fast path (no auth configured)
_ANONYMOUS_RESULT: AuthResult | None = None
_ANONYMOUS_IDENTITY: CallerIdentity | None = None


def set_authenticator(authenticator: CompositeAuthenticator | None) -> None:
    """Set the global authenticator instance."""
    global _authenticator, _ANONYMOUS_RESULT, _ANONYMOUS_IDENTITY
    _authenticator = authenticator

    # Pre-create anonymous singletons for fast path
    if authenticator is None:
        _ANONYMOUS_RESULT = AuthResult.anonymous()
        _ANONYMOUS_IDENTITY = CallerIdentity()  # All None = anonymous
    else:
        _ANONYMOUS_RESULT = None
        _ANONYMOUS_IDENTITY = None


def get_authenticator() -> CompositeAuthenticator | None:
    """Get the global authenticator instance."""
    return _authenticator


async def get_auth_result(request: Request) -> AuthResult:
    """
    FastAPI dependency that performs authentication.

    Returns AuthResult (success, failure, or anonymous).
    """
    # Fast path - no authenticator configured
    if _authenticator is None:
        return _ANONYMOUS_RESULT  # type: ignore  # Pre-created singleton

    return await _authenticator.authenticate(request)


async def get_caller_identity(
    request: Request,
    auth_result: Annotated[AuthResult, Depends(get_auth_result)],
) -> CallerIdentity:
    """
    FastAPI dependency that returns CallerIdentity from authentication.

    This is the main dependency to use in endpoints.
    """
    # Fast path - no auth, no identity headers
    if _authenticator is None:
        app_id = request.headers.get("X-App-ID")
        team = request.headers.get("X-Team")
        if not app_id and not team:
            return _ANONYMOUS_IDENTITY  # type: ignore  # Pre-created singleton
        # Has identity headers, create minimal identity
        return CallerIdentity(app_id=app_id, team=team)

    if auth_result.success:
        # Build CallerIdentity from auth result
        return CallerIdentity(
            user_id=auth_result.principal if auth_result.principal != "anonymous" else None,
            service_id=auth_result.claims.get("client_id"),
            app_id=request.headers.get("X-App-ID"),
            team=request.headers.get("X-Team") or auth_result.claims.get("team"),
            claims=auth_result.claims,
        )
    else:
        # Authentication failed - return 401
        raise HTTPException(
            status_code=401,
            detail=auth_result.error or "Authentication failed",
            headers=_get_auth_headers(),
        )


async def require_auth(
    auth_result: Annotated[AuthResult, Depends(get_auth_result)],
) -> AuthResult:
    """
    FastAPI dependency that requires authentication (no anonymous).

    Use this when you need to enforce authentication even if
    the global config allows anonymous.
    """
    if not auth_result.success:
        raise HTTPException(
            status_code=401,
            detail=auth_result.error or "Authentication required",
            headers=_get_auth_headers(),
        )

    if auth_result.principal == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers=_get_auth_headers(),
        )

    return auth_result


def _get_auth_headers() -> dict[str, str]:
    """Get WWW-Authenticate headers for 401 response."""
    if _authenticator is None:
        return {}

    headers = {}
    challenges = _authenticator.get_challenge_headers()

    if challenges:
        # Combine all challenges into one header
        # Format: WWW-Authenticate: Negotiate, Bearer realm="..."
        header_values = [v for _, v in challenges]
        headers["WWW-Authenticate"] = ", ".join(header_values)

    return headers


def create_unauthorized_response(detail: str = "Unauthorized") -> JSONResponse:
    """Create a 401 response with proper WWW-Authenticate headers."""
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "detail": detail},
        headers=_get_auth_headers(),
    )
