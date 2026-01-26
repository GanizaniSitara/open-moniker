"""Authentication module for moniker service.

Supports Kerberos SPNEGO and Okta JWT authentication methods.
"""

from .config import AuthConfig, KerberosConfig, OktaJWTConfig
from .authenticator import (
    AuthMethod,
    AuthResult,
    Authenticator,
    CompositeAuthenticator,
    create_composite_authenticator,
)
from .dependencies import (
    get_auth_result,
    get_caller_identity,
    require_auth,
    set_authenticator,
    get_authenticator,
    create_unauthorized_response,
)
from .kerberos import KerberosAuthenticator
from .jwt import JWTAuthenticator

__all__ = [
    # Config
    "AuthConfig",
    "KerberosConfig",
    "OktaJWTConfig",
    # Authenticator base
    "AuthMethod",
    "AuthResult",
    "Authenticator",
    "CompositeAuthenticator",
    "create_composite_authenticator",
    # Implementations
    "KerberosAuthenticator",
    "JWTAuthenticator",
    # Dependencies
    "get_auth_result",
    "get_caller_identity",
    "require_auth",
    "set_authenticator",
    "get_authenticator",
    "create_unauthorized_response",
]
