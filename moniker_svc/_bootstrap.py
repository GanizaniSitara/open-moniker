"""Shared initialisation helpers extracted from main.py lifespan.

Each function constructs exactly one component from the service stack.
Both resolver_app.py and management_app.py call these; main.py's own
lifespan was also refactored to use them so all three entry points stay
in sync.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _expand_env_vars(s: str) -> str:
    """Expand ``${VAR}`` and ``${VAR:-default}`` in *s* from the environment."""
    import re

    def _replace(m):
        name, default = m.group(1), m.group(3)
        return os.environ.get(name, default if default is not None else m.group(0))

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:-(.*?))?\}", _replace, s)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(config_path: str | None = None):
    """Load config from file or fall back to defaults.

    Returns ``(config, resolved_config_path)`` where *resolved_config_path*
    is the string that was actually used (needed to resolve relative paths
    such as ``catalog.definition_file``).
    """
    from .config import Config

    config_path = config_path or os.environ.get("MONIKER_CONFIG", "config.yaml")
    if Path(config_path).exists():
        config = Config.from_yaml(config_path)
        logger.info("Loaded config from %s", config_path)
    else:
        config = Config()
        logger.info("Using default config (no file at %s)", config_path)
    return config, config_path


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

def build_catalog_registry(config, config_path: str):
    """Load catalog from YAML or fall back to the demo catalog.

    Returns ``(catalog, catalog_dir, catalog_definition_path)`` where
    *catalog_dir* is the parent directory of the YAML file (used to
    resolve relative SQL/Excel paths in source bindings).
    """
    from .catalog.loader import load_catalog

    catalog_definition_path: Path | None = None
    if config.catalog.definition_file:
        config_dir = Path(config_path).parent.resolve()
        definition_file = _expand_env_vars(config.catalog.definition_file)
        catalog_definition_path = (config_dir / definition_file).resolve()
        logger.info("Loading catalog from: %s", catalog_definition_path)
        catalog = load_catalog(str(catalog_definition_path))
        catalog_dir = catalog_definition_path.parent
    else:
        # Defer import of create_demo_catalog to avoid circular-import at
        # module level (main imports _bootstrap; _bootstrap → main is fine
        # inside a function).
        from .main import create_demo_catalog  # noqa: PLC0415

        logger.info("Using demo catalog (no definition_file configured)")
        catalog = create_demo_catalog()
        catalog_dir = Path.cwd()

    logger.info("Catalog loaded with %d paths", len(catalog.all_paths()))
    return catalog, catalog_dir, catalog_definition_path


# ---------------------------------------------------------------------------
# Domain registry
# ---------------------------------------------------------------------------

def build_domain_registry():
    """Load domain registry from YAML.

    Returns ``(registry, domains_yaml_path)``.  The path is returned so the
    caller can pass it to ``domain_routes.configure()``.
    """
    from .domains import DomainRegistry, load_domains_from_yaml

    domains_yaml_path = os.environ.get("DOMAINS_CONFIG", "domains.yaml")
    registry = DomainRegistry()
    if Path(domains_yaml_path).exists():
        domains = load_domains_from_yaml(domains_yaml_path, registry)
        logger.info("Loaded %d domains from %s", len(domains), domains_yaml_path)
    else:
        logger.info(
            "No domains config found at %s, starting with empty registry",
            domains_yaml_path,
        )
    return registry, domains_yaml_path


# ---------------------------------------------------------------------------
# Application registry
# ---------------------------------------------------------------------------

def build_application_registry():
    """Load application registry from YAML.

    Returns ``(registry, applications_yaml_path)``.  The path is returned so
    the caller can pass it to ``application_routes.configure()``.
    """
    from .applications import ApplicationRegistry, load_applications_from_yaml

    applications_yaml_path = os.environ.get("APPLICATIONS_CONFIG", "applications.yaml")
    registry = ApplicationRegistry()
    if Path(applications_yaml_path).exists():
        apps = load_applications_from_yaml(applications_yaml_path, registry)
        logger.info("Loaded %d applications from %s", len(apps), applications_yaml_path)
    elif Path("sample_applications.yaml").exists():
        apps = load_applications_from_yaml("sample_applications.yaml", registry)
        logger.info("Loaded %d applications from sample_applications.yaml", len(apps))
    else:
        logger.info(
            "No applications config found at %s, starting with empty registry",
            applications_yaml_path,
        )
    return registry, applications_yaml_path


# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

def build_cache(config):
    """Build the in-memory result cache."""
    from .cache.memory import InMemoryCache

    return InMemoryCache(
        max_size=config.cache.max_size,
        default_ttl_seconds=config.cache.default_ttl_seconds,
    )


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

async def build_telemetry(config):
    """Create, wire, and return ``(TelemetryEmitter, TelemetryBatcher)``.

    The caller is responsible for:
    - calling ``await emitter.start()``
    - spawning ``asyncio.create_task(emitter.process_loop())``
    - spawning ``asyncio.create_task(batcher.timer_loop())``
    """
    from .telemetry.batcher import TelemetryBatcher, create_batched_consumer
    from .telemetry.emitter import TelemetryEmitter
    from .telemetry.sinks.console import ConsoleSink
    from .telemetry.sinks.file import RotatingFileSink
    from .telemetry.sinks.zmq import ZmqSink

    emitter = TelemetryEmitter(max_queue_size=config.telemetry.max_queue_size)

    sink_type = config.telemetry.sink_type
    sink_config = config.telemetry.sink_config

    if sink_type == "console":
        sink = ConsoleSink(**sink_config)
    elif sink_type == "file":
        sink = RotatingFileSink(**sink_config)
    elif sink_type == "zmq":
        sink = ZmqSink(**sink_config)
        await sink.start()
    else:
        sink = ConsoleSink()

    batcher = TelemetryBatcher(
        batch_size=config.telemetry.batch_size,
        flush_interval_seconds=config.telemetry.flush_interval_seconds,
        sink=sink.send,
    )
    emitter.add_consumer(create_batched_consumer(batcher))
    return emitter, batcher


# ---------------------------------------------------------------------------
# MonikerService
# ---------------------------------------------------------------------------

def build_service(catalog, cache, emitter, config):
    """Construct and return the MonikerService."""
    from .service import MonikerService

    return MonikerService(catalog=catalog, cache=cache, telemetry=emitter, config=config)


# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------

def build_rate_limiter(config):
    """Build rate limiter.  Returns ``None`` if the governance module is absent."""
    try:
        from .governance.rate_limiter import RateLimiter, RateLimiterConfig

        gov = config.governance
        return RateLimiter(config=RateLimiterConfig(
            enabled=gov.rate_limiter_enabled,
            requests_per_second=gov.requests_per_second,
            burst_capacity=gov.burst_capacity,
            global_requests_per_second=gov.global_requests_per_second,
            global_burst_capacity=gov.global_burst_capacity,
        ))
    except ImportError:
        return None


def build_circuit_breaker(config):
    """Build circuit breaker.  Returns ``None`` if the governance module is absent."""
    try:
        from .governance.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

        return CircuitBreaker(config=CircuitBreakerConfig())
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def configure_auth(config) -> None:
    """Configure the process-global authenticator singleton."""
    from .auth import create_composite_authenticator, set_authenticator

    if config.auth.enabled:
        authenticator = create_composite_authenticator(config.auth)
        set_authenticator(authenticator)
        logger.info("Authentication enabled (enforce=%s)", config.auth.enforce)
    else:
        set_authenticator(None)
        logger.info("Authentication disabled")


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

def build_model_registry(config):
    """Load business-model registry from YAML if enabled.

    Returns ``(registry, models_yaml_path)``.
    """
    from .models import ModelRegistry, load_models_from_yaml

    registry = ModelRegistry()
    models_yaml_path = (
        config.models.definition_file
        or os.environ.get("MODELS_CONFIG", "models.yaml")
    )
    if config.models.enabled:
        if Path(models_yaml_path).exists():
            models = load_models_from_yaml(models_yaml_path, registry)
            logger.info("Loaded %d business models from %s", len(models), models_yaml_path)
        else:
            logger.info(
                "No models config found at %s, starting with empty registry",
                models_yaml_path,
            )
    else:
        logger.info("Business models disabled")
    return registry, models_yaml_path


# ---------------------------------------------------------------------------
# Request registry
# ---------------------------------------------------------------------------

def build_request_registry(config):
    """Load request/approval registry from YAML if enabled.

    Returns ``(registry, requests_yaml_path)``.
    """
    from .requests import RequestRegistry, load_requests_from_yaml

    registry = RequestRegistry()
    requests_yaml_path = (
        config.requests.definition_file
        or os.environ.get("REQUESTS_CONFIG", "requests.yaml")
    )
    if config.requests.enabled:
        if Path(requests_yaml_path).exists():
            loaded_reqs = load_requests_from_yaml(requests_yaml_path, registry)
            logger.info("Loaded %d requests from %s", len(loaded_reqs), requests_yaml_path)
        else:
            logger.info(
                "No requests config found at %s, starting with empty registry",
                requests_yaml_path,
            )
    else:
        logger.info("Request & approval workflow disabled")
    return registry, requests_yaml_path


# ---------------------------------------------------------------------------
# Redis cache
# ---------------------------------------------------------------------------

async def setup_redis(config):
    """Connect to Redis and return the cache handle.

    Returns a ``RedisCache`` instance (connected if Redis is reachable).
    """
    from .cache.redis import RedisCache

    redis_cache = RedisCache(config.redis)
    redis_connected = await redis_cache.connect()

    if not redis_connected:
        logger.info("Redis not available")
    return redis_cache
