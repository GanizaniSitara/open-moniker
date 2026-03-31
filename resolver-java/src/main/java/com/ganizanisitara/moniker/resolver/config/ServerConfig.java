package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Server configuration.
 */
@Data
public class ServerConfig {
    private String host = "0.0.0.0";
    private int port = 8054;
    private int workers = 4;
    private boolean reload = false;

    @SuppressWarnings("unchecked")
    public static ServerConfig fromMap(Map<String, Object> data) {
        if (data == null) return new ServerConfig();
        ServerConfig config = new ServerConfig();
        if (data.containsKey("host")) config.setHost((String) data.get("host"));
        if (data.containsKey("port")) config.setPort(((Number) data.get("port")).intValue());
        if (data.containsKey("workers")) config.setWorkers(((Number) data.get("workers")).intValue());
        if (data.containsKey("reload")) config.setReload((Boolean) data.get("reload"));
        return config;
    }
}
