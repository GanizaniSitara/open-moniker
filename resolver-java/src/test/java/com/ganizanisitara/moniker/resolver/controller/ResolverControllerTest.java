package com.ganizanisitara.moniker.resolver.controller;

import com.ganizanisitara.moniker.resolver.catalog.*;
import com.ganizanisitara.moniker.resolver.config.ApplicationConfig;
import com.ganizanisitara.moniker.resolver.service.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.*;

import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Controller tests using @WebMvcTest and MockMvc.
 */
@WebMvcTest(ResolverController.class)
class ResolverControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private MonikerService monikerService;

    @MockitoBean
    private CatalogRegistry catalog;

    @MockitoBean
    private ApplicationConfig applicationConfig;

    // ---- /ping ----

    @Test
    void pingReturns200Pong() throws Exception {
        mockMvc.perform(get("/ping"))
                .andExpect(status().isOk())
                .andExpect(content().string("pong"));
    }

    // ---- /health ----

    @Test
    void healthReturns200WithStatusField() throws Exception {
        when(catalog.size()).thenReturn(5);

        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("healthy"))
                .andExpect(jsonPath("$.service").value("resolver-java"))
                .andExpect(jsonPath("$.catalog_nodes").value(5));
    }

    // ---- /resolve/{path} ----

    @Test
    void resolveKnownPathReturns200() throws Exception {
        ResolveResult result = new ResolveResult("prices.equity/AAPL", "prices.equity/AAPL");
        result.setSourceType("snowflake");
        result.setSourceConfig(Map.of("database", "MARKET_DATA"));

        when(monikerService.resolve(eq("prices.equity/AAPL"))).thenReturn(result);

        mockMvc.perform(get("/resolve/prices.equity/AAPL"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.path").value("prices.equity/AAPL"))
                .andExpect(jsonPath("$.sourceType").value("snowflake"));
    }

    @Test
    void resolveUnknownReturns404() throws Exception {
        when(monikerService.resolve(anyString()))
                .thenThrow(new ResolutionException("No source binding found for path: unknown/path", 404));

        mockMvc.perform(get("/resolve/unknown/path"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value(containsString("No source binding found")));
    }

    // ---- /describe/{path} ----

    @Test
    void describeReturns200() throws Exception {
        DescribeResult result = new DescribeResult("prices.equity/AAPL");
        result.setDisplayName("Apple Inc.");
        result.setDescription("Apple equity price data");
        result.setStatus(NodeStatus.ACTIVE);
        result.setLeaf(true);

        when(monikerService.describe(eq("prices.equity/AAPL"))).thenReturn(result);

        mockMvc.perform(get("/describe/prices.equity/AAPL"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.path").value("prices.equity/AAPL"))
                .andExpect(jsonPath("$.displayName").value("Apple Inc."));
    }

    // ---- /list/{path} ----

    @Test
    void listChildrenReturns200() throws Exception {
        when(monikerService.listChildren(eq("prices.equity")))
                .thenReturn(List.of("prices.equity/AAPL", "prices.equity/MSFT"));

        mockMvc.perform(get("/list/prices.equity"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.path").value("prices.equity"))
                .andExpect(jsonPath("$.children", hasSize(2)))
                .andExpect(jsonPath("$.count").value(2));
    }

    // ---- /catalog ----

    @Test
    void catalogListReturns200() throws Exception {
        CatalogNode node = new CatalogNode();
        node.setPath("prices.equity/AAPL");
        node.setDisplayName("Apple Inc.");
        node.setStatus(NodeStatus.ACTIVE);

        when(catalog.getAllNodes()).thenReturn(List.of(node));

        mockMvc.perform(get("/catalog"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(1))
                .andExpect(jsonPath("$.nodes", hasSize(1)));
    }

    // ---- /catalog/search ----

    @Test
    void searchReturnsResults() throws Exception {
        CatalogNode node = new CatalogNode();
        node.setPath("prices.equity/AAPL");
        node.setDisplayName("Apple Inc.");
        node.setDescription("Apple equity price data");
        node.setStatus(NodeStatus.ACTIVE);

        when(catalog.getAllNodes()).thenReturn(List.of(node));

        mockMvc.perform(get("/catalog/search").param("q", "apple"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.query").value("apple"))
                .andExpect(jsonPath("$.count").value(1))
                .andExpect(jsonPath("$.results", hasSize(1)));
    }

    @Test
    void searchNoMatchReturnsEmptyResults() throws Exception {
        CatalogNode node = new CatalogNode();
        node.setPath("prices.equity/AAPL");
        node.setDisplayName("Apple Inc.");
        node.setDescription("Apple equity price data");
        node.setStatus(NodeStatus.ACTIVE);

        when(catalog.getAllNodes()).thenReturn(List.of(node));

        mockMvc.perform(get("/catalog/search").param("q", "zzzznotfound"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.count").value(0))
                .andExpect(jsonPath("$.results", hasSize(0)));
    }

    // ---- /catalog/stats ----

    @Test
    void statsReturnsCounts() throws Exception {
        Map<String, Object> stats = new HashMap<>();
        stats.put("total_nodes", 10);
        stats.put("leaf_nodes", 7);
        stats.put("category_nodes", 3);
        stats.put("by_status", Map.of("active", 8, "deprecated", 2));

        when(monikerService.getStats()).thenReturn(stats);

        mockMvc.perform(get("/catalog/stats"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total_nodes").value(10))
                .andExpect(jsonPath("$.leaf_nodes").value(7));
    }
}
