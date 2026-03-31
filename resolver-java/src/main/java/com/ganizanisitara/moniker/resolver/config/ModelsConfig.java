package com.ganizanisitara.moniker.resolver.config;

import lombok.Data;

import java.util.Map;

/**
 * Models registry configuration.
 */
@Data
public class ModelsConfig {
    private boolean enabled = false;
    private String definitionFile = "";

    @SuppressWarnings("unchecked")
    public static ModelsConfig fromMap(Map<String, Object> data) {
        if (data == null) return new ModelsConfig();
        ModelsConfig config = new ModelsConfig();
        if (data.containsKey("enabled")) config.setEnabled((Boolean) data.get("enabled"));
        if (data.containsKey("definition_file")) config.setDefinitionFile((String) data.get("definition_file"));
        return config;
    }
}
