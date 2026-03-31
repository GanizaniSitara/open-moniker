package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Governance / rate-limiting configuration.
 */
@Data
public class GovernanceConfig {
    private boolean rateLimiterEnabled = false;
    private double requestsPerSecond = 100.0;
    private int burstCapacity = 200;
    private double globalRequestsPerSecond = 1000.0;
    private int globalBurstCapacity = 2000;

    @SuppressWarnings("unchecked")
    public static GovernanceConfig fromMap(Map<String, Object> data) {
        if (data == null) return new GovernanceConfig();
        GovernanceConfig config = new GovernanceConfig();
        if (data.containsKey("rate_limiter_enabled")) config.setRateLimiterEnabled((Boolean) data.get("rate_limiter_enabled"));
        if (data.containsKey("requests_per_second")) config.setRequestsPerSecond(((Number) data.get("requests_per_second")).doubleValue());
        if (data.containsKey("burst_capacity")) config.setBurstCapacity(((Number) data.get("burst_capacity")).intValue());
        if (data.containsKey("global_requests_per_second")) config.setGlobalRequestsPerSecond(((Number) data.get("global_requests_per_second")).doubleValue());
        if (data.containsKey("global_burst_capacity")) config.setGlobalBurstCapacity(((Number) data.get("global_burst_capacity")).intValue());
        return config;
    }
}
