"""Kerberos SPNEGO authenticator."""

from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from starlette.requests import Request

from .authenticator import AuthMethod, AuthResult, Authenticator

if TYPE_CHECKING:
    from .config import KerberosConfig

logger = logging.getLogger(__name__)

# Optional gssapi import
try:
    import gssapi
    from gssapi.raw import ChannelBindings
    GSSAPI_AVAILABLE = True
except ImportError:
    gssapi = None  # type: ignore
    ChannelBindings = None  # type: ignore
    GSSAPI_AVAILABLE = False


@dataclass
class KerberosAuthenticator(Authenticator):
    """
    Kerberos SPNEGO authenticator.

    Validates Negotiate tokens using gssapi and extracts the principal name.

    SPNEGO Flow:
    1. Client sends request without auth → Server returns 401 + WWW-Authenticate: Negotiate
    2. Client obtains Kerberos ticket → Sends Authorization: Negotiate <base64-token>
    3. Server validates via gssapi → Extracts principal → Returns AuthResult
    """
    config: KerberosConfig
    _server_creds: object | None = None

    def __post_init__(self) -> None:
        """Initialize server credentials if gssapi is available."""
        if not GSSAPI_AVAILABLE:
            logger.warning("gssapi not available - Kerberos authentication disabled")
            return

        if not self.config.enabled:
            return

        try:
            self._init_credentials()
        except Exception as e:
            logger.error(f"Failed to initialize Kerberos credentials: {e}")

    def _init_credentials(self) -> None:
        """Initialize server credentials from keytab."""
        if not GSSAPI_AVAILABLE or gssapi is None:
            return

        # Set keytab path if configured
        if self.config.keytab_path:
            os.environ["KRB5_KTNAME"] = self.config.keytab_path
            logger.info(f"Using keytab: {self.config.keytab_path}")

        # Create server credentials
        if self.config.service_principal:
            # Use specific service principal
            server_name = gssapi.Name(
                self.config.service_principal,
                name_type=gssapi.NameType.kerberos_principal,
            )
            self._server_creds = gssapi.Credentials(
                name=server_name,
                usage="accept",
            )
            logger.info(f"Initialized Kerberos credentials for: {self.config.service_principal}")
        else:
            # Use default credentials from keytab
            self._server_creds = gssapi.Credentials(usage="accept")
            logger.info("Initialized Kerberos credentials from default keytab")

    @property
    def method(self) -> AuthMethod:
        return AuthMethod.KERBEROS

    async def authenticate(self, request: Request) -> AuthResult | None:
        """
        Authenticate a request using Kerberos SPNEGO.

        Returns None if no Negotiate header present (let other methods try).
        Returns AuthResult on success or failure.
        """
        if not GSSAPI_AVAILABLE:
            return None

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Negotiate "):
            return None

        # Extract the SPNEGO token
        token_b64 = auth_header[10:]  # Skip "Negotiate "
        try:
            token = base64.b64decode(token_b64)
        except Exception as e:
            logger.debug(f"Failed to decode Negotiate token: {e}")
            return AuthResult.failed("Invalid Negotiate token encoding")

        # Validate the token
        try:
            principal = self._validate_token(token)
            if principal:
                return AuthResult.authenticated(
                    principal=principal,
                    method=AuthMethod.KERBEROS,
                    claims={"auth_method": "kerberos"},
                )
            else:
                return AuthResult.failed("Kerberos validation failed")
        except Exception as e:
            logger.warning(f"Kerberos authentication error: {e}")
            return AuthResult.failed(str(e))

    def _validate_token(self, token: bytes) -> str | None:
        """Validate SPNEGO token and extract principal name."""
        if not GSSAPI_AVAILABLE or gssapi is None:
            return None

        try:
            # Create security context
            server_ctx = gssapi.SecurityContext(
                creds=self._server_creds,
                usage="accept",
            )

            # Process the token
            server_ctx.step(token)

            # Check if context is complete
            if server_ctx.complete:
                # Extract the client principal
                if server_ctx.initiator_name:
                    principal = str(server_ctx.initiator_name)
                    logger.debug(f"Kerberos authentication successful: {principal}")
                    return principal

            return None

        except gssapi.exceptions.GSSError as e:
            logger.debug(f"GSSAPI error: {e}")
            raise

    def get_challenge_header(self) -> tuple[str, str] | None:
        """Return WWW-Authenticate: Negotiate header."""
        if not GSSAPI_AVAILABLE or not self.config.enabled:
            return None
        return ("WWW-Authenticate", "Negotiate")
