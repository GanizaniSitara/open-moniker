package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/ganizanisitara/open-moniker/resolver-go/internal/cache"
	"github.com/ganizanisitara/open-moniker/resolver-go/internal/catalog"
	"github.com/ganizanisitara/open-moniker/resolver-go/internal/config"
	"github.com/ganizanisitara/open-moniker/resolver-go/internal/service"
)

// --- Test fixtures ---

func newTestConfig() *config.Config {
	return &config.Config{
		ProjectName: "test",
		Server:      config.ServerConfig{Host: "localhost", Port: 8080},
		Cache:       config.CacheConfig{Enabled: true, DefaultTTLSeconds: 60},
	}
}

func newTestRegistry() *catalog.Registry {
	r := catalog.NewRegistry()

	// Parent domain node
	prices := &catalog.CatalogNode{
		Path:        "prices",
		DisplayName: "Prices",
		Description: "Market prices data",
		Status:      catalog.NodeStatusActive,
		IsLeaf:      false,
		Ownership: &catalog.Ownership{
			AccountableOwner: strPtr("team-prices"),
		},
	}
	r.Register(prices)

	// Leaf node with source binding
	equity := &catalog.CatalogNode{
		Path:        "prices/equity",
		DisplayName: "Equity Prices",
		Description: "Stock equity prices",
		Status:      catalog.NodeStatusActive,
		IsLeaf:      true,
		Tags:        []string{"market-data", "equities"},
		SourceBinding: &catalog.SourceBinding{
			SourceType: catalog.SourceTypeSnowflake,
			Config: map[string]interface{}{
				"database": "MARKET_DATA",
				"schema":   "PRICES",
				"table":    "EQUITY",
			},
			ReadOnly: true,
		},
	}
	r.Register(equity)

	// Another leaf for search/list tests
	fx := &catalog.CatalogNode{
		Path:        "prices/fx",
		DisplayName: "FX Rates",
		Description: "Foreign exchange rates",
		Status:      catalog.NodeStatusActive,
		IsLeaf:      true,
		SourceBinding: &catalog.SourceBinding{
			SourceType: catalog.SourceTypeOracle,
			Config:     map[string]interface{}{"dsn": "oracle://localhost/fx"},
			ReadOnly:   true,
		},
	}
	r.Register(fx)

	return r
}

func strPtr(s string) *string {
	return &s
}

func newTestService(reg *catalog.Registry) *service.MonikerService {
	cacheInst := cache.NewInMemory(60 * time.Second)
	cfg := newTestConfig()
	return service.NewMonikerService(reg, cacheInst, cfg)
}

// Helper to decode JSON response body
func decodeResponse(t *testing.T, rec *httptest.ResponseRecorder) map[string]interface{} {
	t.Helper()
	var result map[string]interface{}
	if err := json.NewDecoder(rec.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response body: %v", err)
	}
	return result
}

// --- ResolveHandler tests ---

func TestResolveKnownPath(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewResolveHandler(svc)

	req := httptest.NewRequest("GET", "/resolve/prices/equity", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	source, ok := result["source"].(map[string]interface{})
	if !ok {
		t.Fatal("expected 'source' field in response")
	}
	if source["source_type"] != "snowflake" {
		t.Errorf("expected source_type 'snowflake', got %v", source["source_type"])
	}
}

func TestResolveUnknownPath(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewResolveHandler(svc)

	req := httptest.NewRequest("GET", "/resolve/nonexistent/path", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Errorf("expected 404, got %d", rec.Code)
	}
}

func TestResolveMissingPath(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewResolveHandler(svc)

	req := httptest.NewRequest("GET", "/resolve/", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", rec.Code)
	}
}

// --- DescribeHandler tests ---

func TestDescribeKnownPath(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewDescribeHandler(svc)

	req := httptest.NewRequest("GET", "/describe/prices/equity", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	if result["path"] != "prices/equity" {
		t.Errorf("expected path 'prices/equity', got %v", result["path"])
	}
	if result["has_source_binding"] != true {
		t.Errorf("expected has_source_binding=true, got %v", result["has_source_binding"])
	}
}

func TestDescribeUnknownPath(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewDescribeHandler(svc)

	req := httptest.NewRequest("GET", "/describe/nonexistent", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	// Describe returns 200 even for unknown paths (returns nil node with ownership info)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	if result["has_source_binding"] != false {
		t.Errorf("expected has_source_binding=false for unknown path, got %v", result["has_source_binding"])
	}
}

// --- ListHandler tests ---

func TestListChildren(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewListHandler(svc)

	req := httptest.NewRequest("GET", "/list/prices", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	children, ok := result["children"].([]interface{})
	if !ok {
		t.Fatal("expected 'children' array in response")
	}
	if len(children) != 2 {
		t.Errorf("expected 2 children, got %d", len(children))
	}
}

// --- CatalogListHandler tests ---

func TestCatalogList(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewCatalogListHandler(svc, reg)

	req := httptest.NewRequest("GET", "/catalog", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	paths, ok := result["paths"].([]interface{})
	if !ok {
		t.Fatal("expected 'paths' array in response")
	}
	if len(paths) != 3 {
		t.Errorf("expected 3 paths, got %d", len(paths))
	}

	total := result["total"].(float64)
	if int(total) != 3 {
		t.Errorf("expected total=3, got %v", total)
	}
}

// --- SearchCatalogHandler tests ---

func TestSearchCatalog(t *testing.T) {
	reg := newTestRegistry()
	handler := NewSearchCatalogHandler(reg)

	req := httptest.NewRequest("GET", "/catalog/search?q=equity", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	if result["query"] != "equity" {
		t.Errorf("expected query='equity', got %v", result["query"])
	}

	count := result["count"].(float64)
	if int(count) == 0 {
		t.Error("expected at least 1 search result")
	}
}

func TestSearchCatalogMissingQuery(t *testing.T) {
	reg := newTestRegistry()
	handler := NewSearchCatalogHandler(reg)

	req := httptest.NewRequest("GET", "/catalog/search", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", rec.Code)
	}
}

// --- CatalogStatsHandler tests ---

func TestCatalogStats(t *testing.T) {
	reg := newTestRegistry()
	handler := NewCatalogStatsHandler(reg)

	req := httptest.NewRequest("GET", "/catalog/stats", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	byStatus, ok := result["by_status"].(map[string]interface{})
	if !ok {
		t.Fatal("expected 'by_status' map in response")
	}
	total := byStatus["total"].(float64)
	if int(total) != 3 {
		t.Errorf("expected total=3, got %v", total)
	}

	bySource, ok := result["by_source_type"].(map[string]interface{})
	if !ok {
		t.Fatal("expected 'by_source_type' map in response")
	}
	// 2 nodes have source bindings: snowflake and oracle
	if len(bySource) != 2 {
		t.Errorf("expected 2 source types, got %d", len(bySource))
	}
}

// --- BatchResolveHandler tests ---

func TestBatchResolve(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewBatchResolveHandler(svc)

	body := map[string]interface{}{
		"monikers": []string{"prices/equity", "prices/fx"},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/resolve/batch", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	results, ok := result["results"].([]interface{})
	if !ok {
		t.Fatal("expected 'results' array in response")
	}
	if len(results) != 2 {
		t.Errorf("expected 2 results, got %d", len(results))
	}
}

func TestBatchResolveEmptyList(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewBatchResolveHandler(svc)

	body := map[string]interface{}{
		"monikers": []string{},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/resolve/batch", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", rec.Code)
	}
}

func TestBatchResolveWithErrors(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewBatchResolveHandler(svc)

	body := map[string]interface{}{
		"monikers": []string{"prices/equity", "nonexistent/path"},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/resolve/batch", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	results := result["results"].([]interface{})

	// Second result should have an error
	second := results[1].(map[string]interface{})
	if _, hasError := second["error"]; !hasError {
		t.Error("expected error in second result for nonexistent path")
	}
}

// --- LineageHandler tests ---

func TestLineage(t *testing.T) {
	reg := newTestRegistry()
	svc := newTestService(reg)
	handler := NewLineageHandler(svc, reg)

	req := httptest.NewRequest("GET", "/lineage/prices/equity", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	if result["path"] != "prices/equity" {
		t.Errorf("expected path 'prices/equity', got %v", result["path"])
	}

	hierarchy, ok := result["hierarchy"].([]interface{})
	if !ok {
		t.Fatal("expected 'hierarchy' array")
	}
	if len(hierarchy) != 2 {
		t.Errorf("expected 2 hierarchy entries, got %d", len(hierarchy))
	}
}

// --- CacheStatusHandler tests ---

func TestCacheStatus(t *testing.T) {
	handler := NewCacheStatusHandler()

	req := httptest.NewRequest("GET", "/cache/status", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	result := decodeResponse(t, rec)
	if result["status"] != "ok" {
		t.Errorf("expected status 'ok', got %v", result["status"])
	}
}

// --- UIHandler tests ---

func TestUIHandler(t *testing.T) {
	handler := NewUIHandler()

	req := httptest.NewRequest("GET", "/ui", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	contentType := rec.Header().Get("Content-Type")
	if contentType != "text/html" {
		t.Errorf("expected Content-Type 'text/html', got %q", contentType)
	}
}

// --- TreeHandler tests ---

func TestTreeHandler(t *testing.T) {
	reg := newTestRegistry()
	handler := NewTreeHandler(reg)

	req := httptest.NewRequest("GET", "/tree/prices", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := decodeResponse(t, rec)
	count := result["count"].(float64)
	if int(count) != 2 {
		t.Errorf("expected 2 children, got %v", count)
	}
}

// --- Content type ---

func TestResponseContentType(t *testing.T) {
	reg := newTestRegistry()
	handler := NewCatalogStatsHandler(reg)

	req := httptest.NewRequest("GET", "/catalog/stats", nil)
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	ct := rec.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected Content-Type 'application/json', got %q", ct)
	}
}
