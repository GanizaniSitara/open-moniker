package com.ganizanisitara.moniker.resolver.service;

import com.ganizanisitara.moniker.resolver.catalog.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for MonikerService.
 */
class MonikerServiceTest {

    private CatalogRegistry catalog;
    private MonikerService service;

    @BeforeEach
    void setUp() {
        catalog = new CatalogRegistry();
        service = new MonikerService(catalog);

        // Register a category node "prices.equity"
        CatalogNode category = new CatalogNode();
        category.setPath("prices.equity");
        category.setDisplayName("Equity Prices");
        category.setDescription("Equity price data");
        category.setStatus(NodeStatus.ACTIVE);
        category.setLeaf(false);

        Ownership ownership = new Ownership();
        ownership.setAccountableOwner("equity-team");
        ownership.setSupportChannel("#equity-support");
        category.setOwnership(ownership);

        catalog.register(category);

        // Register a leaf node with source binding "prices.equity/AAPL"
        CatalogNode leaf = new CatalogNode();
        leaf.setPath("prices.equity/AAPL");
        leaf.setDisplayName("Apple Inc.");
        leaf.setDescription("Apple equity price data");
        leaf.setStatus(NodeStatus.ACTIVE);
        leaf.setLeaf(true);
        leaf.setClassification("internal");
        leaf.setTags(List.of("equity", "us", "tech"));
        leaf.setCreatedAt("2025-01-15");
        leaf.setUpdatedAt("2025-06-01");

        SourceBinding binding = new SourceBinding();
        binding.setType(SourceType.SNOWFLAKE);
        Map<String, Object> config = new HashMap<>();
        config.put("database", "MARKET_DATA");
        config.put("schema", "EQUITY");
        config.put("table", "PRICES");
        binding.setConfig(config);
        leaf.setSourceBinding(binding);

        catalog.register(leaf);
    }

    // ---- resolve ----

    @Test
    void resolveKnownPathReturnsResolveResult() throws ResolutionException {
        ResolveResult result = service.resolve("prices.equity/AAPL");

        assertNotNull(result);
        assertEquals("prices.equity/AAPL", result.getPath());
        assertEquals("snowflake", result.getSourceType());
        assertNotNull(result.getSourceConfig());
        assertEquals("MARKET_DATA", result.getSourceConfig().get("database"));
    }

    @Test
    void resolveKnownPathIncludesOwnership() throws ResolutionException {
        ResolveResult result = service.resolve("prices.equity/AAPL");

        assertNotNull(result.getOwnership());
        assertEquals("equity-team", result.getOwnership().getAccountableOwner());
    }

    @Test
    void resolveUnknownPathThrows404() {
        ResolutionException ex = assertThrows(ResolutionException.class, () ->
                service.resolve("nonexistent/path")
        );
        assertEquals(404, ex.getStatusCode());
        assertTrue(ex.getMessage().contains("No source binding found"));
    }

    @Test
    void resolveInvalidMonikerThrows400() {
        ResolutionException ex = assertThrows(ResolutionException.class, () ->
                service.resolve("")
        );
        assertEquals(400, ex.getStatusCode());
        assertTrue(ex.getMessage().contains("Invalid moniker"));
    }

    // ---- describe ----

    @Test
    void describeReturnsDescribeResult() throws ResolutionException {
        DescribeResult result = service.describe("prices.equity/AAPL");

        assertNotNull(result);
        assertEquals("prices.equity/AAPL", result.getPath());
        assertEquals("Apple Inc.", result.getDisplayName());
        assertEquals("Apple equity price data", result.getDescription());
        assertEquals(NodeStatus.ACTIVE, result.getStatus());
        assertEquals("internal", result.getClassification());
        assertTrue(result.isLeaf());
        assertTrue(result.isHasSourceBinding());
        assertEquals("2025-01-15", result.getCreatedAt());
    }

    @Test
    void describeUnknownPathThrows404() {
        ResolutionException ex = assertThrows(ResolutionException.class, () ->
                service.describe("unknown/node")
        );
        assertEquals(404, ex.getStatusCode());
        assertTrue(ex.getMessage().contains("Node not found"));
    }

    // ---- listChildren ----

    @Test
    void listChildrenReturnsChildPaths() {
        List<String> children = service.listChildren("prices.equity");
        assertNotNull(children);
        assertEquals(1, children.size());
        assertTrue(children.contains("prices.equity/AAPL"));
    }

    @Test
    void listChildrenReturnsEmptyForLeaf() {
        List<String> children = service.listChildren("prices.equity/AAPL");
        assertNotNull(children);
        assertTrue(children.isEmpty());
    }

    // ---- getLineage ----

    @Test
    void getLineageReturnsAncestorChain() {
        List<Map<String, Object>> lineage = service.getLineage("prices.equity/AAPL");
        assertNotNull(lineage);
        // Should include "prices.equity" and "prices.equity/AAPL" (root-to-leaf)
        assertTrue(lineage.size() >= 2);

        // First entry should be the ancestor
        assertEquals("prices.equity", lineage.get(0).get("path"));
        // Last entry should be the node itself
        assertEquals("prices.equity/AAPL", lineage.get(lineage.size() - 1).get("path"));
    }

    // ---- getStats ----

    @Test
    void getStatsReturnsCounts() {
        Map<String, Object> stats = service.getStats();

        assertNotNull(stats);
        assertEquals(2, stats.get("total_nodes"));
        assertEquals(1, stats.get("leaf_nodes"));
        assertEquals(1, stats.get("category_nodes"));

        @SuppressWarnings("unchecked")
        Map<String, Integer> byStatus = (Map<String, Integer>) stats.get("by_status");
        assertNotNull(byStatus);
        assertEquals(2, byStatus.get("active"));

        @SuppressWarnings("unchecked")
        Map<String, Integer> bySourceType = (Map<String, Integer>) stats.get("by_source_type");
        assertNotNull(bySourceType);
        assertEquals(1, bySourceType.get("snowflake"));
    }

    // ---- deprecated node resolution ----

    @Test
    void resolveDeprecatedNodeIncludesDeprecationInfo() throws ResolutionException {
        // Register a deprecated node with source binding
        CatalogNode deprecated = new CatalogNode();
        deprecated.setPath("legacy/feed");
        deprecated.setDisplayName("Legacy Feed");
        deprecated.setDescription("Old feed");
        deprecated.setStatus(NodeStatus.DEPRECATED);
        deprecated.setLeaf(true);
        deprecated.setDeprecationMessage("Use new/feed instead");

        SourceBinding binding = new SourceBinding();
        binding.setType(SourceType.REST);
        binding.setConfig(Map.of("url", "https://api.example.com/legacy"));
        deprecated.setSourceBinding(binding);

        catalog.register(deprecated);

        ResolveResult result = service.resolve("legacy/feed");
        assertTrue(result.isDeprecated());
        assertEquals("Use new/feed instead", result.getDeprecationMessage());
    }
}
