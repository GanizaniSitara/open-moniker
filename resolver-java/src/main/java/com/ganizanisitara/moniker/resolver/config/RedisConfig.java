package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Redis configuration for query result caching.
 */
@Data
public class RedisConfig {
    private boolean enabled = false;
    private String host = "localhost";
    private int port = 6379;
    private int db = 0;
    private String password = "";
    private String prefix = "moniker:cache:";
    private double socketTimeout = 5.0;
    private double socketConnectTimeout = 5.0;

    @SuppressWarnings("unchecked")
    public static RedisConfig fromMap(Map<String, Object> data) {
        if (data == null) return new RedisConfig();
        RedisConfig config = new RedisConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("host")) config.setHost((String) data.get("host"));
        if (data.containsKey("port")) config.setPort(((Number) data.get("port")).intValue());
        if (data.containsKey("db")) config.setDb(((Number) data.get("db")).intValue());
        if (data.containsKey("password")) config.setPassword((String) data.get("password"));
        if (data.containsKey("prefix")) config.setPrefix((String) data.get("prefix"));
        if (data.containsKey("socket_timeout")) config.setSocketTimeout(((Number) data.get("socket_timeout")).doubleValue());
        if (data.containsKey("socket_connect_timeout")) config.setSocketConnectTimeout(((Number) data.get("socket_connect_timeout")).doubleValue());
        return config;
    }
}
