package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.HashMap;
import java.util.Map;

/**
 * Telemetry configuration.
 */
@Data
public class TelemetryConfig {
    private boolean enabled = false;
    private String sinkType = "console";
    private Map<String, Object> sinkConfig = new HashMap<>();
    private int batchSize = 100;
    private double flushIntervalSeconds = 5.0;
    private int maxQueueSize = 10000;

    @SuppressWarnings("unchecked")
    public static TelemetryConfig fromMap(Map<String, Object> data) {
        if (data == null) return new TelemetryConfig();
        TelemetryConfig config = new TelemetryConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("sink_type")) config.setSinkType((String) data.get("sink_type"));
        if (data.containsKey("sink_config")) {
            Object sc = data.get("sink_config");
            if (sc instanceof Map) {
                config.setSinkConfig((Map<String, Object>) sc);
            }
        }
        if (data.containsKey("batch_size")) config.setBatchSize(((Number) data.get("batch_size")).intValue());
        if (data.containsKey("flush_interval_seconds")) config.setFlushIntervalSeconds(((Number) data.get("flush_interval_seconds")).doubleValue());
        if (data.containsKey("max_queue_size")) config.setMaxQueueSize(((Number) data.get("max_queue_size")).intValue());
        return config;
    }
}
