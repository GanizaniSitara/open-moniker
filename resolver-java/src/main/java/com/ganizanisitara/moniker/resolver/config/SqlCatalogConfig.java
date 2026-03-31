package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * SQL Catalog configuration for importing and browsing SQL by schema/table taxonomy.
 */
@Data
public class SqlCatalogConfig {
    private boolean enabled = false;
    private String dbPath = "sql_catalog.db";
    private String sourceDbPath = "";

    @SuppressWarnings("unchecked")
    public static SqlCatalogConfig fromMap(Map<String, Object> data) {
        if (data == null) return new SqlCatalogConfig();
        SqlCatalogConfig config = new SqlCatalogConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("db_path")) config.setDbPath((String) data.get("db_path"));
        if (data.containsKey("source_db_path")) config.setSourceDbPath((String) data.get("source_db_path"));
        return config;
    }
}
