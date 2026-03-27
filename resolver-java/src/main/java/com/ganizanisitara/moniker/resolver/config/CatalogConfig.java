package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Catalog configuration.
 */
@Data
public class CatalogConfig {
    private String definitionFile = "../catalog.yaml";
    private int reloadIntervalSeconds = 60;

    @SuppressWarnings("unchecked")
    public static CatalogConfig fromMap(Map<String, Object> data) {
        if (data == null) return new CatalogConfig();
        CatalogConfig config = new CatalogConfig();
        if (data.containsKey("definition_file")) config.setDefinitionFile((String) data.get("definition_file"));
        if (data.containsKey("reload_interval_seconds")) config.setReloadIntervalSeconds(((Number) data.get("reload_interval_seconds")).intValue());
        return config;
    }
}
