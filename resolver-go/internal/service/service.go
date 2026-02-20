package service

import (
	"context"
	"fmt"
	"strings"

	"github.com/ganizanisitara/open-moniker-svc/resolver-go/internal/cache"
	"github.com/ganizanisitara/open-moniker-svc/resolver-go/internal/catalog"
	"github.com/ganizanisitara/open-moniker-svc/resolver-go/internal/config"
	"github.com/ganizanisitara/open-moniker-svc/resolver-go/internal/moniker"
)

const maxSuccessorDepth = 5

// MonikerService provides moniker resolution
type MonikerService struct {
	catalog *catalog.Registry
	cache   *cache.InMemory
	config  *config.Config
}

// NewMonikerService creates a new moniker service
func NewMonikerService(reg *catalog.Registry, cacheInst *cache.InMemory, cfg *config.Config) *MonikerService {
	return &MonikerService{
		catalog: reg,
		cache:   cacheInst,
		config:  cfg,
	}
}

// Resolve resolves a moniker to its source binding
func (s *MonikerService) Resolve(ctx context.Context, monikerStr string, caller *CallerIdentity) (*ResolveResult, error) {
	// Parse moniker
	m, err := moniker.ParseMoniker(monikerStr)
	if err != nil {
		return nil, &ResolutionError{Message: fmt.Sprintf("Invalid moniker: %v", err)}
	}

	// Get the path
	path := m.CanonicalPath()

	// Find source binding (walk hierarchy if needed)
	binding, bindingPath := s.catalog.FindSourceBinding(path)
	if binding == nil {
		return nil, &NotFoundError{Path: path}
	}

	// Check for successor redirect
	node := s.catalog.Get(bindingPath)
	if node != nil && node.Status == catalog.NodeStatusDeprecated && node.Successor != nil {
		// Follow successor chain (with depth limit)
		successorPath := *node.Successor
		for depth := 0; depth < maxSuccessorDepth; depth++ {
			successorNode := s.catalog.Get(successorPath)
			if successorNode == nil {
				break
			}
			if successorNode.Status != catalog.NodeStatusDeprecated || successorNode.Successor == nil {
				// Found non-deprecated successor
				binding, bindingPath = s.catalog.FindSourceBinding(successorPath)
				if binding != nil {
					// Redirect successful
					redirectFrom := path
					path = successorPath
					node = successorNode

					result := s.buildResolveResult(m, path, binding, bindingPath, node)
					result.RedirectedFrom = &redirectFrom
					return result, nil
				}
				break
			}
			successorPath = *successorNode.Successor
		}
	}

	// Validate access policy if present
	if node != nil && node.AccessPolicy != nil {
		segments := m.Path.Segments
		allowed, message, estimatedRows := node.AccessPolicy.Validate(segments)
		if !allowed {
			return nil, &AccessDeniedError{
				Message:       *message,
				EstimatedRows: &estimatedRows,
			}
		}
	}

	// Build result
	result := s.buildResolveResult(m, path, binding, bindingPath, node)
	return result, nil
}

func (s *MonikerService) buildResolveResult(m *moniker.Moniker, path string, binding *catalog.SourceBinding, bindingPath string, node *catalog.CatalogNode) *ResolveResult {
	// Resolve ownership
	ownership := s.catalog.ResolveOwnership(path)

	// Build resolved source
	source := &ResolvedSource{
		SourceType: string(binding.SourceType),
		Connection: make(map[string]interface{}),
		Params:     make(map[string]interface{}),
		ReadOnly:   binding.ReadOnly,
	}

	// Copy config to connection (excluding query)
	for k, v := range binding.Config {
		if k != "query" {
			source.Connection[k] = v
		}
	}

	// Get query from config
	if queryVal, ok := binding.Config["query"]; ok {
		if queryStr, ok := queryVal.(string); ok {
			// Simple placeholder substitution
			formattedQuery := s.formatQuery(queryStr, m)
			source.Query = &formattedQuery
		}
	}

	// Set schema if present
	if binding.Schema != nil {
		source.Schema = binding.Schema
	}

	// Calculate sub-path if binding is at ancestor
	var subPath *string
	if bindingPath != path {
		// Path is longer than binding path
		if strings.HasPrefix(path, bindingPath+"/") {
			sp := strings.TrimPrefix(path, bindingPath+"/")
			subPath = &sp
		}
	}

	return &ResolveResult{
		Moniker:     m.String(),
		Path:        path,
		Source:      source,
		Ownership:   ownership,
		Node:        node,
		BindingPath: bindingPath,
		SubPath:     subPath,
	}
}

// formatQuery performs basic placeholder substitution
func (s *MonikerService) formatQuery(query string, m *moniker.Moniker) string {
	result := query

	// Replace {segments[N]} placeholders
	for i, seg := range m.Path.Segments {
		placeholder := fmt.Sprintf("{segments[%d]}", i)
		result = strings.ReplaceAll(result, placeholder, seg)
	}

	// Replace {version_date} if present
	if m.VersionDate() != nil {
		result = strings.ReplaceAll(result, "{version_date}", *m.VersionDate())
	}

	// Replace {is_latest} if present
	isLatest := "false"
	if m.IsLatest() {
		isLatest = "true"
	}
	result = strings.ReplaceAll(result, "{is_latest}", isLatest)

	return result
}

// Describe returns metadata about a path
func (s *MonikerService) Describe(ctx context.Context, path string) (*DescribeResult, error) {
	node := s.catalog.Get(path)
	ownership := s.catalog.ResolveOwnership(path)

	// Check if has source binding
	binding, _ := s.catalog.FindSourceBinding(path)
	hasBinding := binding != nil

	var sourceType *string
	if binding != nil {
		st := string(binding.SourceType)
		sourceType = &st
	}

	return &DescribeResult{
		Node:             node,
		Ownership:        ownership,
		Moniker:          fmt.Sprintf("moniker://%s", path),
		Path:             path,
		HasSourceBinding: hasBinding,
		SourceType:       sourceType,
	}, nil
}

// List returns children of a path
func (s *MonikerService) List(ctx context.Context, path string) (*ListResult, error) {
	childrenPaths := s.catalog.ChildrenPaths(path)
	ownership := s.catalog.ResolveOwnership(path)

	return &ListResult{
		Children:  childrenPaths,
		Moniker:   fmt.Sprintf("moniker://%s", path),
		Path:      path,
		Ownership: ownership,
	}, nil
}
