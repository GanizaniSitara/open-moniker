package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

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
    private RedisConfig redis = new RedisConfig();
    private DeprecationConfig deprecation = new DeprecationConfig();
    private ModelsConfig models = new ModelsConfig();
    private RequestsConfig requests = new RequestsConfig();
    private GovernanceConfig governance = new GovernanceConfig();
    private SqlCatalogConfig sqlCatalog = new SqlCatalogConfig();

    @SuppressWarnings("unchecked")
    public static ApplicationConfig fromMap(Map<String, Object> data) {
        if (data == null) return new ApplicationConfig();
        ApplicationConfig config = new ApplicationConfig();

        if (data.containsKey("project_name")) config.setProjectName((String) data.get("project_name"));

        config.setServer(ServerConfig.fromMap((Map<String, Object>) data.get("server")));
        config.setTelemetry(TelemetryConfig.fromMap((Map<String, Object>) data.get("telemetry")));
        config.setCache(CacheConfig.fromMap((Map<String, Object>) data.get("cache")));
        config.setCatalog(CatalogConfig.fromMap((Map<String, Object>) data.get("catalog")));
        config.setAuth(AuthConfig.fromMap((Map<String, Object>) data.get("auth")));
        config.setConfigUi(ConfigUIConfig.fromMap((Map<String, Object>) data.get("config_ui")));
        config.setRedis(RedisConfig.fromMap((Map<String, Object>) data.get("redis")));
        config.setDeprecation(DeprecationConfig.fromMap((Map<String, Object>) data.get("deprecation")));
        config.setModels(ModelsConfig.fromMap((Map<String, Object>) data.get("models")));
        config.setRequests(RequestsConfig.fromMap((Map<String, Object>) data.get("requests")));
        config.setGovernance(GovernanceConfig.fromMap((Map<String, Object>) data.get("governance")));
        config.setSqlCatalog(SqlCatalogConfig.fromMap((Map<String, Object>) data.get("sql_catalog")));

        return config;
    }
}
