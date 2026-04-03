package moniker

import (
	"fmt"
	"strings"
)

// SegmentID represents an in-path identity parameter (@id).
// For example, positions@ACC001 → Index=1, Value="ACC001"
type SegmentID struct {
	Index int    // which positional segment carries the @id
	Value string // the identity value after @
}

// MonikerPath represents a hierarchical path to a data asset
type MonikerPath struct {
	Segments []string
}

// NewMonikerPath creates a new MonikerPath from segments
func NewMonikerPath(segments []string) *MonikerPath {
	return &MonikerPath{Segments: segments}
}

// RootPath returns an empty root path
func RootPath() *MonikerPath {
	return &MonikerPath{Segments: []string{}}
}

// String returns the path as a slash-separated string
func (p *MonikerPath) String() string {
	return strings.Join(p.Segments, "/")
}

// Len returns the number of segments
func (p *MonikerPath) Len() int {
	return len(p.Segments)
}

// IsEmpty returns true if the path has no segments
func (p *MonikerPath) IsEmpty() bool {
	return len(p.Segments) == 0
}

// Domain returns the first segment (the data domain)
func (p *MonikerPath) Domain() *string {
	if len(p.Segments) == 0 {
		return nil
	}
	domain := p.Segments[0]
	return &domain
}

// Parent returns the parent path, or nil if at root
func (p *MonikerPath) Parent() *MonikerPath {
	if len(p.Segments) <= 1 {
		return nil
	}
	return &MonikerPath{Segments: p.Segments[:len(p.Segments)-1]}
}

// Leaf returns the final segment of the path
func (p *MonikerPath) Leaf() *string {
	if len(p.Segments) == 0 {
		return nil
	}
	leaf := p.Segments[len(p.Segments)-1]
	return &leaf
}

// Ancestors returns all ancestor paths from root to parent (not including self)
func (p *MonikerPath) Ancestors() []*MonikerPath {
	result := make([]*MonikerPath, 0, len(p.Segments)-1)
	for i := 1; i < len(p.Segments); i++ {
		result = append(result, &MonikerPath{Segments: p.Segments[:i]})
	}
	return result
}

// Child creates a child path by appending a segment
func (p *MonikerPath) Child(segment string) *MonikerPath {
	newSegments := make([]string, len(p.Segments)+1)
	copy(newSegments, p.Segments)
	newSegments[len(p.Segments)] = segment
	return &MonikerPath{Segments: newSegments}
}

// IsAncestorOf checks if this path is an ancestor of another
func (p *MonikerPath) IsAncestorOf(other *MonikerPath) bool {
	if len(p.Segments) >= len(other.Segments) {
		return false
	}
	for i := range p.Segments {
		if p.Segments[i] != other.Segments[i] {
			return false
		}
	}
	return true
}

// IsDescendantOf checks if this path is a descendant of another
func (p *MonikerPath) IsDescendantOf(other *MonikerPath) bool {
	return other.IsAncestorOf(p)
}

// FromString parses a path string into a MonikerPath
func FromString(pathStr string) *MonikerPath {
	if pathStr == "" || pathStr == "/" {
		return RootPath()
	}
	// Strip leading/trailing slashes and split
	clean := strings.Trim(pathStr, "/")
	if clean == "" {
		return RootPath()
	}
	segments := strings.Split(clean, "/")
	return &MonikerPath{Segments: segments}
}

// QueryParams holds query parameters for a moniker
type QueryParams map[string]string

// Get returns a query parameter value
func (q QueryParams) Get(key string, defaultVal *string) *string {
	if val, ok := q[key]; ok {
		return &val
	}
	return defaultVal
}

// Has checks if a query parameter exists
func (q QueryParams) Has(key string) bool {
	_, ok := q[key]
	return ok
}

// IsEmpty returns true if there are no parameters
func (q QueryParams) IsEmpty() bool {
	return len(q) == 0
}

// Moniker represents a complete moniker reference
type Moniker struct {
	Path            *MonikerPath
	Namespace       *string
	SegmentID       *SegmentID // In-path identity parameter (@id)
	DateParam       *string    // date@VALUE: "20260101", "latest", "3M", etc.
	FilterShortlink *string    // filter@CODE that was expanded (e.g. "filter@xK9f2p")
	Revision        *int
	Params          QueryParams
}

// String returns the canonical moniker string
func (m *Moniker) String() string {
	var parts []string

	// Namespace prefix
	if m.Namespace != nil {
		parts = append(parts, *m.Namespace+"@")
	}

	// Path (with @id re-injected)
	parts = append(parts, m.pathWithSegmentID())

	// Date segment (before revision)
	if m.DateParam != nil {
		parts = append(parts, "/date@"+*m.DateParam)
	}

	// Revision suffix
	if m.Revision != nil {
		parts = append(parts, fmt.Sprintf("/v%d", *m.Revision))
	}

	base := strings.Join(parts, "")

	// Query params
	if len(m.Params) > 0 {
		var paramParts []string
		for k, v := range m.Params {
			paramParts = append(paramParts, fmt.Sprintf("%s=%s", k, v))
		}
		return fmt.Sprintf("moniker://%s?%s", base, strings.Join(paramParts, "&"))
	}

	return "moniker://" + base
}

// pathWithSegmentID returns the path string with @id re-injected into the correct segment
func (m *Moniker) pathWithSegmentID() string {
	pathStr := m.Path.String()
	if m.SegmentID == nil {
		return pathStr
	}
	segments := strings.Split(pathStr, "/")
	if m.SegmentID.Index < len(segments) {
		segments[m.SegmentID.Index] = segments[m.SegmentID.Index] + "@" + m.SegmentID.Value
	}
	return strings.Join(segments, "/")
}

// Domain returns the data domain (first path segment)
func (m *Moniker) Domain() *string {
	return m.Path.Domain()
}

// CanonicalPath returns the path as a string (without @id, namespace, or params)
func (m *Moniker) CanonicalPath() string {
	return m.Path.String()
}

// FullPath returns path including @id and revision but not namespace
func (m *Moniker) FullPath() string {
	parts := []string{m.pathWithSegmentID()}
	if m.Revision != nil {
		parts = append(parts, fmt.Sprintf("/v%d", *m.Revision))
	}
	return strings.Join(parts, "")
}

// WithNamespace creates a copy with a different namespace
func (m *Moniker) WithNamespace(namespace *string) *Moniker {
	return &Moniker{
		Path:            m.Path,
		Namespace:       namespace,
		SegmentID:       m.SegmentID,
		DateParam:       m.DateParam,
		FilterShortlink: m.FilterShortlink,
		Revision:        m.Revision,
		Params:          m.Params,
	}
}
