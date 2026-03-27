package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Requests registry configuration.
 */
@Data
public class RequestsConfig {
    private boolean enabled = false;
    private String definitionFile = "";

    @SuppressWarnings("unchecked")
    public static RequestsConfig fromMap(Map<String, Object> data) {
        if (data == null) return new RequestsConfig();
        RequestsConfig config = new RequestsConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("definition_file")) config.setDefinitionFile((String) data.get("definition_file"));
        return config;
    }
}
