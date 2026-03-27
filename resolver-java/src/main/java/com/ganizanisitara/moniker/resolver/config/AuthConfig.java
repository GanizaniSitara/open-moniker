package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Authentication configuration.
 */
@Data
public class AuthConfig {
    private boolean enabled = false;
    private boolean enforce = false;
    private List<String> methodOrder = new ArrayList<>();

    @SuppressWarnings("unchecked")
    public static AuthConfig fromMap(Map<String, Object> data) {
        if (data == null) return new AuthConfig();
        AuthConfig config = new AuthConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("enforce")) config.setEnforce((Boolean) data.get("enforce"));
        if (data.containsKey("method_order")) {
            Object mo = data.get("method_order");
            if (mo instanceof List) {
                config.setMethodOrder((List<String>) mo);
            }
        }
        return config;
    }
}
