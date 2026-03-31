package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Config UI configuration.
 */
@Data
public class ConfigUIConfig {
    private boolean enabled = false;
    private String yamlOutputPath = "";
    private boolean showFilePaths = true;

    @SuppressWarnings("unchecked")
    public static ConfigUIConfig fromMap(Map<String, Object> data) {
        if (data == null) return new ConfigUIConfig();
        ConfigUIConfig config = new ConfigUIConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("yaml_output_path")) config.setYamlOutputPath((String) data.get("yaml_output_path"));
        if (data.containsKey("show_file_paths")) config.setShowFilePaths((Boolean) data.get("show_file_paths"));
        return config;
    }
}
