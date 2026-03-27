package com.ganizanisitara.moniker.resolver.catalog;

/**
 * Supported data source types.
 */
public enum SourceType {
    SNOWFLAKE("snowflake"),
    ORACLE("oracle"),
    MSSQL("mssql"),               // Microsoft SQL Server
    REST("rest"),
    STATIC("static"),
    EXCEL("excel"),
    BLOOMBERG("bloomberg"),
    REFINITIV("refinitiv"),
    OPENSEARCH("opensearch"),     // OpenSearch/Elasticsearch
    COMPOSITE("composite"),       // Combines multiple sources
    DERIVED("derived"),           // Computed from other monikers
    FRED("fred"),                 // Federal Reserve Economic Data
    YFINANCE("yfinance");         // Yahoo Finance

    private final String value;

    SourceType(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

    @Override
    public String toString() {
        return value;
    }

    /**
     * Parse a source type from string. Returns STATIC for unknown types
     * (matching Python's graceful fallback behavior).
     */
    public static SourceType fromString(String value) {
        for (SourceType type : SourceType.values()) {
            if (type.value.equalsIgnoreCase(value)) {
                return type;
            }
        }
        // Graceful fallback to STATIC for unknown types
        return STATIC;
    }
}
