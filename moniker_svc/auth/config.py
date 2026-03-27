"""Authentication configuration dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KerberosConfig:
    """Kerberos SPNEGO authentication configuration."""
    enabled: bool = False
    service_principal: str | None = None  # e.g., "HTTP/moniker-svc.firm.com@FIRM.COM"
    keytab_path: str | None = None  # e.g., "/etc/moniker-svc/krb5.keytab"
    realm: str | None = None  # e.g., "FIRM.COM"


@dataclass
class OktaJWTConfig:
    """Okta JWT authentication configuration."""
    enabled: bool = False
    issuer: str | None = None  # e.g., "https://firm.okta.com/oauth2/default"
    audience: str | None = None  # e.g., "api://moniker-svc"
    jwks_cache_ttl: int = 3600  # seconds
    user_claim: str = "sub"
    groups_claim: str = "groups"

    # Test mode: use symmetric secret instead of JWKS (for local dev only!)
    # Set issuer to "test" and provide test_secret to enable
    test_secret: str | None = None  # Shared secret for HS256 signing


@dataclass
class AuthConfig:
    """Main authentication configuration."""
    enabled: bool = False
    enforce: bool = False  # If False, allow anonymous fallback
    method_order: list[str] = field(default_factory=lambda: ["kerberos", "jwt"])

    kerberos: KerberosConfig = field(default_factory=KerberosConfig)
    okta: OktaJWTConfig = field(default_factory=OktaJWTConfig)

    @classmethod
    def from_dict(cls, data: dict) -> AuthConfig:
        """Create config from dictionary."""
        kerberos_data = data.get("kerberos", {})
        okta_data = data.get("okta", {})

        return cls(
            enabled=data.get("enabled", False),
            enforce=data.get("enforce", False),
            method_order=data.get("method_order", ["kerberos", "jwt"]),
            kerberos=KerberosConfig(**kerberos_data),
            okta=OktaJWTConfig(**okta_data),
        )
