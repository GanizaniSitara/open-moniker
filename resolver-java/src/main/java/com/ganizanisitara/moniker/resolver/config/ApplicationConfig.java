package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

/**
 * Root configuration object.
 */
@Data
public class ApplicationConfig {
    private String projectName = "Moniker Service";
    private ServerConfig server = new ServerConfig();
    private TelemetryConfig telemetry = new TelemetryConfig();
    private CacheConfig cache = new CacheConfig();
    private CatalogConfig catalog = new CatalogConfig();
    private AuthConfig auth = new AuthConfig();
    private ConfigUIConfig configUi = new ConfigUIConfig();
}
