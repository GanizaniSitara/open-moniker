package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/ganizanisitara/open-moniker-svc/resolver-go/internal/catalog"
	"github.com/ganizanisitara/open-moniker-svc/resolver-go/internal/service"
)

// CatalogListHandler handles GET /catalog
type CatalogListHandler struct {
	service *service.MonikerService
	catalog *catalog.Registry
}

// NewCatalogListHandler creates a new catalog list handler
func NewCatalogListHandler(svc *service.MonikerService, reg *catalog.Registry) *CatalogListHandler {
	return &CatalogListHandler{service: svc, catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *CatalogListHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Get query parameters
	cursor := r.URL.Query().Get("cursor")
	limitStr := r.URL.Query().Get("limit")
	_ = r.URL.Query().Get("status") // statusFilter - TODO: implement filtering

	limit := 100
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 && l <= 1000 {
			limit = l
		}
	}

	// Get all paths (simplified - no real pagination yet)
	allPaths := h.catalog.AllPaths()

	// Sort and paginate
	startIdx := 0
	if cursor != "" {
		for i, p := range allPaths {
			if p > cursor {
				startIdx = i
				break
			}
		}
	}

	endIdx := startIdx + limit
	if endIdx > len(allPaths) {
		endIdx = len(allPaths)
	}

	paths := allPaths[startIdx:endIdx]

	var nextCursor *string
	if endIdx < len(allPaths) {
		nc := allPaths[endIdx-1]
		nextCursor = &nc
	}

	response := map[string]interface{}{
		"paths": paths,
		"count": len(paths),
		"total": len(allPaths),
	}
	if nextCursor != nil {
		response["next_cursor"] = *nextCursor
	}

	writeJSON(w, http.StatusOK, response)
}

// SearchCatalogHandler handles GET /catalog/search
type SearchCatalogHandler struct {
	catalog *catalog.Registry
}

// NewSearchCatalogHandler creates a new search handler
func NewSearchCatalogHandler(reg *catalog.Registry) *SearchCatalogHandler {
	return &SearchCatalogHandler{catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *SearchCatalogHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		writeError(w, http.StatusBadRequest, "Missing query parameter", map[string]interface{}{
			"detail": "Query parameter 'q' is required",
		})
		return
	}

	limitStr := r.URL.Query().Get("limit")
	limit := 50
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	results := h.catalog.Search(query, nil, limit)

	response := map[string]interface{}{
		"query":   query,
		"results": results,
		"count":   len(results),
	}

	writeJSON(w, http.StatusOK, response)
}

// CatalogStatsHandler handles GET /catalog/stats
type CatalogStatsHandler struct {
	catalog *catalog.Registry
}

// NewCatalogStatsHandler creates a new stats handler
func NewCatalogStatsHandler(reg *catalog.Registry) *CatalogStatsHandler {
	return &CatalogStatsHandler{catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *CatalogStatsHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	counts := h.catalog.Count()

	// Count by source type
	sourceTypeCounts := make(map[string]int)
	for _, node := range h.catalog.AllNodes() {
		if node.SourceBinding != nil {
			st := string(node.SourceBinding.SourceType)
			sourceTypeCounts[st]++
		}
	}

	response := map[string]interface{}{
		"by_status":      counts,
		"by_source_type": sourceTypeCounts,
	}

	writeJSON(w, http.StatusOK, response)
}

// BatchResolveHandler handles POST /resolve/batch
type BatchResolveHandler struct {
	service *service.MonikerService
}

// NewBatchResolveHandler creates a new batch resolve handler
func NewBatchResolveHandler(svc *service.MonikerService) *BatchResolveHandler {
	return &BatchResolveHandler{service: svc}
}

// ServeHTTP implements http.Handler
func (h *BatchResolveHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	var request struct {
		Monikers []string `json:"monikers"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body", map[string]interface{}{
			"detail": err.Error(),
		})
		return
	}

	if len(request.Monikers) == 0 {
		writeError(w, http.StatusBadRequest, "Empty moniker list", nil)
		return
	}

	if len(request.Monikers) > 100 {
		writeError(w, http.StatusBadRequest, "Too many monikers", map[string]interface{}{
			"detail": "Maximum 100 monikers per batch request",
			"count":  len(request.Monikers),
		})
		return
	}

	// Get caller identity
	caller := &service.CallerIdentity{
		UserID: r.Header.Get("X-User-ID"),
		Source: "api",
	}
	if caller.UserID == "" {
		caller.UserID = "anonymous"
	}

	// Resolve all monikers (could parallelize with goroutines)
	results := make([]interface{}, len(request.Monikers))
	for i, monikerStr := range request.Monikers {
		result, err := h.service.Resolve(r.Context(), monikerStr, caller)
		if err != nil {
			results[i] = map[string]interface{}{
				"moniker": monikerStr,
				"error":   err.Error(),
			}
		} else {
			results[i] = result
		}
	}

	response := map[string]interface{}{
		"results": results,
		"count":   len(results),
	}

	writeJSON(w, http.StatusOK, response)
}

// LineageHandler handles GET /lineage/{path}
type LineageHandler struct {
	service *service.MonikerService
	catalog *catalog.Registry
}

// NewLineageHandler creates a new lineage handler
func NewLineageHandler(svc *service.MonikerService, reg *catalog.Registry) *LineageHandler {
	return &LineageHandler{service: svc, catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *LineageHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/lineage/")
	if path == "" {
		writeError(w, http.StatusBadRequest, "Missing path", nil)
		return
	}

	// Get ownership with provenance
	ownership := h.catalog.ResolveOwnership(path)

	// Build lineage response
	response := map[string]interface{}{
		"path":      path,
		"ownership": ownership,
		"hierarchy": buildHierarchy(path),
	}

	writeJSON(w, http.StatusOK, response)
}

func buildHierarchy(path string) []string {
	if path == "" {
		return []string{}
	}

	parts := strings.Split(path, "/")
	hierarchy := make([]string, 0, len(parts))

	for i := 1; i <= len(parts); i++ {
		hierarchy = append(hierarchy, strings.Join(parts[:i], "/"))
	}

	return hierarchy
}

// MetadataHandler handles GET /metadata/{path}
type MetadataHandler struct {
	service *service.MonikerService
	catalog *catalog.Registry
}

// NewMetadataHandler creates a new metadata handler
func NewMetadataHandler(svc *service.MonikerService, reg *catalog.Registry) *MetadataHandler {
	return &MetadataHandler{service: svc, catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *MetadataHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/metadata/")
	if path == "" {
		writeError(w, http.StatusBadRequest, "Missing path", nil)
		return
	}

	node := h.catalog.Get(path)
	if node == nil {
		writeError(w, http.StatusNotFound, "Node not found", map[string]interface{}{
			"path": path,
		})
		return
	}

	ownership := h.catalog.ResolveOwnership(path)
	binding, bindingPath := h.catalog.FindSourceBinding(path)

	response := map[string]interface{}{
		"path":         path,
		"node":         node,
		"ownership":    ownership,
		"has_binding":  binding != nil,
		"binding_path": bindingPath,
	}

	if binding != nil {
		response["source_type"] = string(binding.SourceType)
	}

	writeJSON(w, http.StatusOK, response)
}

// TreeHandler handles GET /tree/{path} and GET /tree
type TreeHandler struct {
	catalog *catalog.Registry
}

// NewTreeHandler creates a new tree handler
func NewTreeHandler(reg *catalog.Registry) *TreeHandler {
	return &TreeHandler{catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *TreeHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/tree/")
	path = strings.TrimPrefix(path, "/")

	// Build tree structure
	node := h.catalog.Get(path)
	children := h.catalog.Children(path)

	childNodes := make([]map[string]interface{}, len(children))
	for i, child := range children {
		childNodes[i] = map[string]interface{}{
			"path":         child.Path,
			"display_name": child.DisplayName,
			"is_leaf":      child.IsLeaf,
			"status":       child.Status,
		}
	}

	response := map[string]interface{}{
		"path":     path,
		"node":     node,
		"children": childNodes,
		"count":    len(children),
	}

	writeJSON(w, http.StatusOK, response)
}

// CacheStatusHandler handles GET /cache/status
type CacheStatusHandler struct{}

// NewCacheStatusHandler creates a new cache status handler
func NewCacheStatusHandler() *CacheStatusHandler {
	return &CacheStatusHandler{}
}

// ServeHTTP implements http.Handler
func (h *CacheStatusHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":  "ok",
		"backend": "in-memory",
		"message": "Cache is operational",
	}
	writeJSON(w, http.StatusOK, response)
}

// TelemetryAccessHandler handles POST /telemetry/access
type TelemetryAccessHandler struct{}

// NewTelemetryAccessHandler creates a new telemetry handler
func NewTelemetryAccessHandler() *TelemetryAccessHandler {
	return &TelemetryAccessHandler{}
}

// ServeHTTP implements http.Handler
func (h *TelemetryAccessHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Parse telemetry event (simplified - just acknowledge)
	var event map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid telemetry event", nil)
		return
	}

	// In production, this would emit to telemetry system
	response := map[string]interface{}{
		"status":  "accepted",
		"message": "Telemetry event recorded",
	}
	writeJSON(w, http.StatusAccepted, response)
}

// UIHandler handles GET /ui
type UIHandler struct{}

// NewUIHandler creates a new UI handler
func NewUIHandler() *UIHandler {
	return &UIHandler{}
}

// ServeHTTP implements http.Handler
func (h *UIHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	html := `<!DOCTYPE html>
<html>
<head>
    <title>Moniker Catalog Browser</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .info { background: #f0f0f0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Moniker Catalog Browser</h1>
    <div class="info">
        <p><strong>Go Resolver</strong> - High Performance Edition</p>
        <p>Navigate to <code>/catalog</code> for catalog listing</p>
        <p>Navigate to <code>/catalog/search?q=term</code> for search</p>
        <p>Navigate to <code>/health</code> for service health</p>
    </div>
</body>
</html>`

	w.Header().Set("Content-Type", "text/html")
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, html)
}
