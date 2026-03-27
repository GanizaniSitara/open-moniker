package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Deprecation behavior configuration.
 */
@Data
public class DeprecationConfig {
    private boolean enabled = false;
    private boolean redirectOnResolve = false;
    private boolean validatedReload = false;
    private boolean blockBreakingReload = false;
    private boolean deprecationTelemetry = false;

    @SuppressWarnings("unchecked")
    public static DeprecationConfig fromMap(Map<String, Object> data) {
        if (data == null) return new DeprecationConfig();
        DeprecationConfig config = new DeprecationConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("redirect_on_resolve")) config.setRedirectOnResolve((Boolean) data.get("redirect_on_resolve"));
        if (data.containsKey("validated_reload")) config.setValidatedReload((Boolean) data.get("validated_reload"));
        if (data.containsKey("block_breaking_reload")) config.setBlockBreakingReload((Boolean) data.get("block_breaking_reload"));
        if (data.containsKey("deprecation_telemetry")) config.setDeprecationTelemetry((Boolean) data.get("deprecation_telemetry"));
        return config;
    }
}
