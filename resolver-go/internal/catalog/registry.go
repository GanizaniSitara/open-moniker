package catalog

import (
	"strings"
	"sync"
)

// Registry is a thread-safe registry of catalog nodes
type Registry struct {
	nodes    map[string]*CatalogNode
	children map[string]map[string]bool // parent -> children paths
	mu       sync.RWMutex                // Read-heavy workload
	auditLog []AuditEntry
}

// NewRegistry creates a new empty catalog registry
func NewRegistry() *Registry {
	return &Registry{
		nodes:    make(map[string]*CatalogNode),
		children: make(map[string]map[string]bool),
		auditLog: make([]AuditEntry, 0),
	}
}

// Register registers a catalog node
func (r *Registry) Register(node *CatalogNode) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.nodes[node.Path] = node
	// Update parent's children set
	parentPath := parentPath(node.Path)
	if parentPath != nil {
		if r.children[*parentPath] == nil {
			r.children[*parentPath] = make(map[string]bool)
		}
		r.children[*parentPath][node.Path] = true
	}
}

// RegisterMany registers multiple nodes atomically
func (r *Registry) RegisterMany(nodes []*CatalogNode) {
	r.mu.Lock()
	defer r.mu.Unlock()

	for _, node := range nodes {
		r.nodes[node.Path] = node
		parentPath := parentPath(node.Path)
		if parentPath != nil {
			if r.children[*parentPath] == nil {
				r.children[*parentPath] = make(map[string]bool)
			}
			r.children[*parentPath][node.Path] = true
		}
	}
}

// Get returns a node by path
func (r *Registry) Get(path string) *CatalogNode {
	r.mu.RLock()
	defer r.mu.RUnlock()

	return r.nodes[path]
}

// GetOrVirtual returns a node, or creates a virtual node if it doesn't exist
func (r *Registry) GetOrVirtual(path string) *CatalogNode {
	r.mu.RLock()
	node := r.nodes[path]
	r.mu.RUnlock()

	if node != nil {
		return node
	}

	// Create virtual node (not added to registry)
	return &CatalogNode{
		Path:   path,
		IsLeaf: false,
	}
}

// Exists checks if a path exists in the catalog
func (r *Registry) Exists(path string) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()

	_, exists := r.nodes[path]
	return exists
}

// Children returns direct children of a path
func (r *Registry) Children(path string) []*CatalogNode {
	r.mu.RLock()
	defer r.mu.RUnlock()

	childPaths := r.children[path]
	result := make([]*CatalogNode, 0, len(childPaths))
	for p := range childPaths {
		if node, ok := r.nodes[p]; ok {
			result = append(result, node)
		}
	}
	return result
}

// ChildrenPaths returns paths of direct children
func (r *Registry) ChildrenPaths(path string) []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	childPaths := r.children[path]
	result := make([]string, 0, len(childPaths))
	for p := range childPaths {
		result = append(result, p)
	}
	return result
}

// ResolveOwnership resolves effective ownership for a path by walking up the hierarchy
// Each ownership field inherits independently from the nearest ancestor that defines it
func (r *Registry) ResolveOwnership(path string) *ResolvedOwnership {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Collect all paths from root to this node
	paths := append(ancestorPaths(path), path)

	// Initialize ownership fields
	result := &ResolvedOwnership{}

	// Walk from root to leaf, each level can override
	for _, p := range paths {
		node, ok := r.nodes[p]
		if !ok || node.Ownership == nil {
			continue
		}

		ownership := node.Ownership

		// Simplified ownership
		if ownership.AccountableOwner != nil {
			result.AccountableOwner = ownership.AccountableOwner
			result.AccountableOwnerSource = &p
		}
		if ownership.DataSpecialist != nil {
			result.DataSpecialist = ownership.DataSpecialist
			result.DataSpecialistSource = &p
		}
		if ownership.SupportChannel != nil {
			result.SupportChannel = ownership.SupportChannel
			result.SupportChannelSource = &p
		}

		// Formal governance roles
		if ownership.ADOP != nil {
			result.ADOP = ownership.ADOP
			result.ADOPSource = &p
		}
		if ownership.ADS != nil {
			result.ADS = ownership.ADS
			result.ADSSource = &p
		}
		if ownership.ADAL != nil {
			result.ADAL = ownership.ADAL
			result.ADALSource = &p
		}

		// Human-readable names for governance roles
		if ownership.ADOPName != nil {
			result.ADOPName = ownership.ADOPName
			result.ADOPNameSource = &p
		}
		if ownership.ADSName != nil {
			result.ADSName = ownership.ADSName
			result.ADSNameSource = &p
		}
		if ownership.ADALName != nil {
			result.ADALName = ownership.ADALName
			result.ADALNameSource = &p
		}

		if ownership.UI != nil {
			result.UI = ownership.UI
			result.UISource = &p
		}
	}

	return result
}

// FindSourceBinding finds the source binding for a path
// Returns the binding and the path where it was defined
// If the exact path doesn't have a binding, walks up to find a parent with a binding
func (r *Registry) FindSourceBinding(path string) (*SourceBinding, string) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// First check exact match
	if node, ok := r.nodes[path]; ok && node.SourceBinding != nil {
		// Skip non-resolvable statuses
		if node.Status == NodeStatusArchived || node.Status == NodeStatusDraft || node.Status == NodeStatusPendingReview {
			// Fall through to ancestor check
		} else {
			return node.SourceBinding, path
		}
	}

	// Walk up hierarchy
	ancestors := ancestorPaths(path)
	for i := len(ancestors) - 1; i >= 0; i-- {
		ancestor := ancestors[i]
		if node, ok := r.nodes[ancestor]; ok && node.SourceBinding != nil {
			if node.Status == NodeStatusArchived || node.Status == NodeStatusDraft || node.Status == NodeStatusPendingReview {
				continue
			}
			return node.SourceBinding, ancestor
		}
	}

	return nil, ""
}

// AllPaths returns all registered paths
func (r *Registry) AllPaths() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	paths := make([]string, 0, len(r.nodes))
	for p := range r.nodes {
		paths = append(paths, p)
	}
	return paths
}

// AllNodes returns all registered nodes
func (r *Registry) AllNodes() []*CatalogNode {
	r.mu.RLock()
	defer r.mu.RUnlock()

	nodes := make([]*CatalogNode, 0, len(r.nodes))
	for _, node := range r.nodes {
		nodes = append(nodes, node)
	}
	return nodes
}

// Clear clears all nodes
func (r *Registry) Clear() {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.nodes = make(map[string]*CatalogNode)
	r.children = make(map[string]map[string]bool)
}

// AtomicReplace atomically replaces all nodes with a new set
// This is for hot reload - build the new catalog, then swap
func (r *Registry) AtomicReplace(newNodes []*CatalogNode) {
	newNodesDict := make(map[string]*CatalogNode)
	newChildren := make(map[string]map[string]bool)

	for _, node := range newNodes {
		newNodesDict[node.Path] = node
		parentPath := parentPath(node.Path)
		if parentPath != nil {
			if newChildren[*parentPath] == nil {
				newChildren[*parentPath] = make(map[string]bool)
			}
			newChildren[*parentPath][node.Path] = true
		}
	}

	r.mu.Lock()
	defer r.mu.Unlock()

	r.nodes = newNodesDict
	r.children = newChildren
}

// FindByStatus returns all nodes with a given lifecycle status
func (r *Registry) FindByStatus(status NodeStatus) []*CatalogNode {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]*CatalogNode, 0)
	for _, node := range r.nodes {
		if node.Status == status {
			result = append(result, node)
		}
	}
	return result
}

// FindActive returns all active (resolvable) nodes
func (r *Registry) FindActive() []*CatalogNode {
	return r.FindByStatus(NodeStatusActive)
}

// FindDeprecated returns all deprecated nodes
func (r *Registry) FindDeprecated() []*CatalogNode {
	return r.FindByStatus(NodeStatusDeprecated)
}

// Search searches catalog nodes by path, display_name, description, or tags
func (r *Registry) Search(query string, status *NodeStatus, limit int) []*CatalogNode {
	queryLower := strings.ToLower(query)

	r.mu.RLock()
	defer r.mu.RUnlock()

	results := make([]*CatalogNode, 0, limit)
	for _, node := range r.nodes {
		if status != nil && node.Status != *status {
			continue
		}

		// Check if query matches path, display name, description, or tags
		if strings.Contains(strings.ToLower(node.Path), queryLower) ||
			strings.Contains(strings.ToLower(node.DisplayName), queryLower) ||
			strings.Contains(strings.ToLower(node.Description), queryLower) {
			results = append(results, node)
			if len(results) >= limit {
				break
			}
			continue
		}

		// Check tags
		for _, tag := range node.Tags {
			if strings.Contains(strings.ToLower(tag), queryLower) {
				results = append(results, node)
				if len(results) >= limit {
					break
				}
				break
			}
		}

		if len(results) >= limit {
			break
		}
	}

	return results
}

// Count returns counts by status
func (r *Registry) Count() map[string]int {
	r.mu.RLock()
	defer r.mu.RUnlock()

	counts := make(map[string]int)
	for _, node := range r.nodes {
		key := string(node.Status)
		counts[key] = counts[key] + 1
	}
	counts["total"] = len(r.nodes)
	return counts
}

// Helper functions

// parentPath returns the parent path, or nil if at root
// Handles both '.' and '/' as hierarchy separators
func parentPath(path string) *string {
	if path == "" {
		return nil
	}

	// Check for '/' first (more specific), then '.'
	if idx := strings.LastIndex(path, "/"); idx != -1 {
		parent := path[:idx]
		return &parent
	}
	if idx := strings.LastIndex(path, "."); idx != -1 {
		parent := path[:idx]
		return &parent
	}

	// Parent is root
	root := ""
	return &root
}

// ancestorPaths returns all ancestor paths from root to parent
// Handles both '.' and '/' as hierarchy separators
// Example: 'analytics.risk/var' -> ['analytics', 'analytics.risk']
func ancestorPaths(path string) []string {
	if path == "" {
		return []string{}
	}

	result := make([]string, 0)
	current := path

	for {
		// Find parent by removing last segment (either after '/' or '.')
		var parent string
		if idx := strings.LastIndex(current, "/"); idx != -1 {
			parent = current[:idx]
		} else if idx := strings.LastIndex(current, "."); idx != -1 {
			parent = current[:idx]
		} else {
			break // No more parents
		}

		if parent != "" {
			// Insert at beginning to maintain root->parent order
			result = append([]string{parent}, result...)
			current = parent
		} else {
			break
		}
	}

	return result
}
