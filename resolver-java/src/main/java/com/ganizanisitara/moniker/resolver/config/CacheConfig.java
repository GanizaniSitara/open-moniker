package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Cache configuration.
 */
@Data
public class CacheConfig {
    private boolean enabled = true;
    private int maxSize = 10000;
    private int defaultTtlSeconds = 300;

    @SuppressWarnings("unchecked")
    public static CacheConfig fromMap(Map<String, Object> data) {
        if (data == null) return new CacheConfig();
        CacheConfig config = new CacheConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("max_size")) config.setMaxSize(((Number) data.get("max_size")).intValue());
        if (data.containsKey("default_ttl_seconds")) config.setDefaultTtlSeconds(((Number) data.get("default_ttl_seconds")).intValue());
        return config;
    }
}
