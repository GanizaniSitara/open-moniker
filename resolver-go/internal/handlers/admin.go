package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/ganizanisitara/open-moniker-svc/resolver-go/internal/catalog"
)

// UpdateStatusHandler handles PUT /catalog/{path}/status
type UpdateStatusHandler struct {
	catalog *catalog.Registry
}

// NewUpdateStatusHandler creates a new update status handler
func NewUpdateStatusHandler(reg *catalog.Registry) *UpdateStatusHandler {
	return &UpdateStatusHandler{catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *UpdateStatusHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Extract path from URL
	path := strings.TrimPrefix(r.URL.Path, "/catalog/")
	path = strings.TrimSuffix(path, "/status")

	if path == "" {
		writeError(w, http.StatusBadRequest, "Missing path", nil)
		return
	}

	// Parse request body
	var request struct {
		Status string `json:"status"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body", nil)
		return
	}

	// Validate status
	validStatuses := map[string]catalog.NodeStatus{
		"draft":          catalog.NodeStatusDraft,
		"pending_review": catalog.NodeStatusPendingReview,
		"approved":       catalog.NodeStatusApproved,
		"active":         catalog.NodeStatusActive,
		"deprecated":     catalog.NodeStatusDeprecated,
		"archived":       catalog.NodeStatusArchived,
	}

	newStatus, ok := validStatuses[request.Status]
	if !ok {
		writeError(w, http.StatusBadRequest, "Invalid status", map[string]interface{}{
			"detail":         "Status must be one of: draft, pending_review, approved, active, deprecated, archived",
			"provided": request.Status,
		})
		return
	}

	// Get node
	node := h.catalog.Get(path)
	if node == nil {
		writeError(w, http.StatusNotFound, "Node not found", map[string]interface{}{
			"path": path,
		})
		return
	}

	// Update status (simplified - in production would validate transitions)
	oldStatus := node.Status
	node.Status = newStatus

	response := map[string]interface{}{
		"path":       path,
		"old_status": string(oldStatus),
		"new_status": string(newStatus),
		"updated":    true,
	}

	writeJSON(w, http.StatusOK, response)
}

// AuditLogHandler handles GET /catalog/{path}/audit
type AuditLogHandler struct {
	catalog *catalog.Registry
}

// NewAuditLogHandler creates a new audit log handler
func NewAuditLogHandler(reg *catalog.Registry) *AuditLogHandler {
	return &AuditLogHandler{catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *AuditLogHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/catalog/")
	path = strings.TrimSuffix(path, "/audit")

	// For now, return empty audit log (would be implemented with actual audit trail)
	response := map[string]interface{}{
		"path":    path,
		"entries": []interface{}{},
		"count":   0,
		"message": "Audit log not yet implemented",
	}

	writeJSON(w, http.StatusOK, response)
}

// FetchDataHandler handles GET /fetch/{path}
type FetchDataHandler struct {
	catalog *catalog.Registry
}

// NewFetchDataHandler creates a new fetch handler
func NewFetchDataHandler(reg *catalog.Registry) *FetchDataHandler {
	return &FetchDataHandler{catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *FetchDataHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/fetch/")

	if path == "" {
		writeError(w, http.StatusBadRequest, "Missing path", nil)
		return
	}

	// This endpoint would actually fetch data from the source
	// For now, return a placeholder
	writeError(w, http.StatusNotImplemented, "Data fetch not implemented", map[string]interface{}{
		"detail": "Server-side data fetch requires adapter implementation",
		"path":   path,
	})
}

// RefreshCacheHandler handles POST /cache/refresh/{path}
type RefreshCacheHandler struct {
	catalog *catalog.Registry
}

// NewRefreshCacheHandler creates a new cache refresh handler
func NewRefreshCacheHandler(reg *catalog.Registry) *RefreshCacheHandler {
	return &RefreshCacheHandler{catalog: reg}
}

// ServeHTTP implements http.Handler
func (h *RefreshCacheHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/cache/refresh/")

	response := map[string]interface{}{
		"path":    path,
		"status":  "ok",
		"message": "Cache refresh triggered (placeholder)",
	}

	writeJSON(w, http.StatusOK, response)
}
