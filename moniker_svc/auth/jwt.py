"""JWT authenticator for Okta tokens."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from starlette.requests import Request

from .authenticator import AuthMethod, AuthResult, Authenticator

if TYPE_CHECKING:
    from .config import OktaJWTConfig

logger = logging.getLogger(__name__)

# Optional jose import
try:
    from jose import jwt, jwk, JWTError
    from jose.exceptions import JWKError
    JOSE_AVAILABLE = True
except ImportError:
    jwt = None  # type: ignore
    jwk = None  # type: ignore
    JWTError = Exception  # type: ignore
    JWKError = Exception  # type: ignore
    JOSE_AVAILABLE = False

# Optional httpx for fetching JWKS
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False


@dataclass
class JWKSCache:
    """Cache for JWKS keys."""
    keys: dict[str, Any] = field(default_factory=dict)
    fetched_at: float = 0.0
    ttl: int = 3600


@dataclass
class JWTAuthenticator(Authenticator):
    """
    JWT authenticator for Okta tokens.

    Validates Bearer tokens using Okta's JWKS endpoint.

    JWT Flow:
    1. Client sends Authorization: Bearer <jwt>
    2. Server fetches/caches JWKS from Okta
    3. Validates signature, issuer, audience, expiry
    4. Extracts claims → Returns AuthResult
    """
    config: OktaJWTConfig
    _jwks_cache: JWKSCache = field(default_factory=JWKSCache)

    def __post_init__(self) -> None:
        """Initialize the authenticator."""
        if not JOSE_AVAILABLE:
            logger.warning("python-jose not available - JWT authentication disabled")
            return

        if not self.config.enabled:
            return

        if not self.config.issuer:
            logger.warning("JWT issuer not configured - JWT authentication disabled")

        # Check for test mode
        if self.config.issuer == "test" and self.config.test_secret:
            logger.warning("JWT test mode enabled - DO NOT USE IN PRODUCTION")

        self._jwks_cache = JWKSCache(ttl=self.config.jwks_cache_ttl)

    @property
    def method(self) -> AuthMethod:
        return AuthMethod.JWT

    async def authenticate(self, request: Request) -> AuthResult | None:
        """
        Authenticate a request using JWT Bearer token.

        Returns None if no Bearer token present (let other methods try).
        Returns AuthResult on success or failure.
        """
        if not JOSE_AVAILABLE:
            return None

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Skip "Bearer "

        try:
            claims = await self._validate_token(token)
            if claims:
                # Extract principal from configured claim
                principal = claims.get(self.config.user_claim, "unknown")

                # Extract groups if present
                groups = claims.get(self.config.groups_claim, [])
                if isinstance(groups, str):
                    groups = [groups]

                return AuthResult.authenticated(
                    principal=str(principal),
                    method=AuthMethod.JWT,
                    groups=groups,
                    claims=claims,
                )
            else:
                return AuthResult.failed("JWT validation failed")

        except JWTError as e:
            logger.debug(f"JWT validation error: {e}")
            return AuthResult.failed(f"Invalid JWT: {e}")
        except Exception as e:
            logger.warning(f"JWT authentication error: {e}")
            return AuthResult.failed(str(e))

    async def _validate_token(self, token: str) -> dict[str, Any] | None:
        """Validate JWT token and return claims."""
        if not JOSE_AVAILABLE or jwt is None:
            return None

        # Test mode - use symmetric secret (HS256)
        if self.config.issuer == "test" and self.config.test_secret:
            return self._validate_test_token(token)

        # Get unverified header to find key ID
        try:
            unverified_header = jwt.get_unverified_header(token)
        except JWTError:
            return None

        kid = unverified_header.get("kid")
        if not kid:
            logger.debug("JWT missing key ID (kid)")
            return None

        # Get signing key from JWKS
        signing_key = await self._get_signing_key(kid)
        if not signing_key:
            return None

        # Validate and decode the token
        try:
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256", "RS384", "RS512"],
                audience=self.config.audience,
                issuer=self.config.issuer,
                options={
                    "verify_aud": self.config.audience is not None,
                    "verify_iss": self.config.issuer is not None,
                    "verify_exp": True,
                    "verify_iat": True,
                },
            )
            return claims
        except JWTError as e:
            logger.debug(f"JWT decode failed: {e}")
            raise

    def _validate_test_token(self, token: str) -> dict[str, Any] | None:
        """Validate token using test secret (HS256). For local dev only."""
        if not JOSE_AVAILABLE or jwt is None:
            return None

        try:
            claims = jwt.decode(
                token,
                self.config.test_secret,
                algorithms=["HS256"],
                audience=self.config.audience,
                issuer="test",
                options={
                    "verify_aud": self.config.audience is not None,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_iat": True,
                },
            )
            return claims
        except JWTError as e:
            logger.debug(f"Test JWT decode failed: {e}")
            raise

    async def _get_signing_key(self, kid: str) -> dict[str, Any] | None:
        """Get signing key from JWKS, with caching."""
        # Check cache
        now = time.time()
        if kid in self._jwks_cache.keys:
            if now - self._jwks_cache.fetched_at < self._jwks_cache.ttl:
                return self._jwks_cache.keys[kid]

        # Fetch JWKS
        jwks = await self._fetch_jwks()
        if not jwks:
            return None

        # Update cache
        self._jwks_cache.keys = {}
        self._jwks_cache.fetched_at = now

        for key_data in jwks.get("keys", []):
            key_id = key_data.get("kid")
            if key_id:
                self._jwks_cache.keys[key_id] = key_data

        return self._jwks_cache.keys.get(kid)

    async def _fetch_jwks(self) -> dict[str, Any] | None:
        """Fetch JWKS from identity provider's well-known endpoint."""
        if not HTTPX_AVAILABLE or httpx is None:
            logger.error("httpx not available - cannot fetch JWKS")
            return None

        if not self.config.issuer:
            return None

        issuer = self.config.issuer.rstrip('/')

        # Try standard .well-known endpoint first (Auth0, generic OIDC)
        # Then fall back to Okta-specific endpoint
        jwks_urls = [
            f"{issuer}/.well-known/jwks.json",  # Auth0, standard OIDC
            f"{issuer}/v1/keys",  # Okta
        ]

        for jwks_url in jwks_urls:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(jwks_url)
                    if response.status_code == 200:
                        logger.debug(f"Fetched JWKS from {jwks_url}")
                        return response.json()
            except Exception as e:
                logger.debug(f"Failed to fetch JWKS from {jwks_url}: {e}")
                continue

        logger.error(f"Failed to fetch JWKS from any endpoint for issuer {issuer}")
        return None

    def get_challenge_header(self) -> tuple[str, str] | None:
        """Return WWW-Authenticate: Bearer header."""
        if not JOSE_AVAILABLE or not self.config.enabled:
            return None

        # Include realm and issuer in challenge
        parts = ["Bearer"]
        if self.config.issuer:
            parts.append(f'realm="{self.config.issuer}"')
        if self.config.audience:
            parts.append(f'scope="{self.config.audience}"')

        return ("WWW-Authenticate", " ".join(parts))
