"""Base authenticator classes and composite authenticator."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

from starlette.requests import Request

if TYPE_CHECKING:
    from .config import AuthConfig

logger = logging.getLogger(__name__)


class AuthMethod(str, Enum):
    """Authentication method used."""
    KERBEROS = "kerberos"
    JWT = "jwt"
    ANONYMOUS = "anonymous"


@dataclass(frozen=True, slots=True)
class AuthResult:
    """Result of an authentication attempt."""
    success: bool
    principal: str | None = None
    method: AuthMethod = AuthMethod.ANONYMOUS
    groups: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def authenticated(
        cls,
        principal: str,
        method: AuthMethod,
        groups: list[str] | None = None,
        claims: dict[str, Any] | None = None,
    ) -> AuthResult:
        """Create a successful authentication result."""
        return cls(
            success=True,
            principal=principal,
            method=method,
            groups=groups or [],
            claims=claims or {},
        )

    @classmethod
    def failed(cls, error: str) -> AuthResult:
        """Create a failed authentication result."""
        return cls(success=False, error=error)

    @classmethod
    def anonymous(cls) -> AuthResult:
        """Create an anonymous authentication result."""
        return cls(
            success=True,
            principal="anonymous",
            method=AuthMethod.ANONYMOUS,
        )


class Authenticator(ABC):
    """Base class for authenticators."""

    @property
    @abstractmethod
    def method(self) -> AuthMethod:
        """Return the authentication method this authenticator handles."""
        ...

    @abstractmethod
    async def authenticate(self, request: Request) -> AuthResult | None:
        """
        Attempt to authenticate the request.

        Returns:
            AuthResult if this authenticator can handle the request (success or failure),
            None if this authenticator doesn't apply to this request.
        """
        ...

    @abstractmethod
    def get_challenge_header(self) -> tuple[str, str] | None:
        """
        Return the WWW-Authenticate challenge header for this method.

        Returns:
            Tuple of (header_name, header_value), or None if no challenge.
        """
        ...


@dataclass
class CompositeAuthenticator:
    """
    Tries multiple authenticators in order.

    First successful authentication wins. If all fail and enforce is False,
    returns anonymous identity.
    """
    authenticators: list[Authenticator] = field(default_factory=list)
    enforce: bool = False

    async def authenticate(self, request: Request) -> AuthResult:
        """
        Authenticate the request using configured authenticators.

        Tries each authenticator in order. First one that returns a result
        (success or failure) wins. If none apply and enforce is False,
        returns anonymous.
        """
        for authenticator in self.authenticators:
            try:
                result = await authenticator.authenticate(request)
                if result is not None:
                    if result.success:
                        logger.debug(
                            f"Authenticated via {authenticator.method.value}: {result.principal}"
                        )
                        return result
                    else:
                        logger.debug(
                            f"Authentication failed via {authenticator.method.value}: {result.error}"
                        )
                        # Continue to next authenticator on failure
            except Exception as e:
                logger.warning(f"Authenticator {authenticator.method.value} error: {e}")
                continue

        # No authenticator handled the request
        if self.enforce:
            return AuthResult.failed("Authentication required")
        else:
            logger.debug("No authentication provided, using anonymous")
            return AuthResult.anonymous()

    def get_challenge_headers(self) -> list[tuple[str, str]]:
        """Get all WWW-Authenticate challenge headers."""
        headers = []
        for authenticator in self.authenticators:
            header = authenticator.get_challenge_header()
            if header:
                headers.append(header)
        return headers


def create_composite_authenticator(config: AuthConfig) -> CompositeAuthenticator:
    """Create a composite authenticator from configuration."""
    from .kerberos import KerberosAuthenticator
    from .jwt import JWTAuthenticator

    authenticators: list[Authenticator] = []

    # Add authenticators in configured order
    for method_name in config.method_order:
        if method_name == "kerberos" and config.kerberos.enabled:
            authenticators.append(KerberosAuthenticator(config.kerberos))
            logger.info("Kerberos authentication enabled")
        elif method_name == "jwt" and config.okta.enabled:
            authenticators.append(JWTAuthenticator(config.okta))
            logger.info("JWT authentication enabled")

    return CompositeAuthenticator(
        authenticators=authenticators,
        enforce=config.enforce,
    )
