package moniker

import (
	"fmt"
	"regexp"
	"strings"
)

// VersionType represents the semantic type of a version specifier
type VersionType string

const (
	VersionTypeDate      VersionType = "date"      // @20260101 (YYYYMMDD format)
	VersionTypeLatest    VersionType = "latest"    // @latest
	VersionTypeLookback  VersionType = "lookback"  // @3M, @12Y, @1W, @5D (lookback period)
	VersionTypeFrequency VersionType = "frequency" // @daily, @weekly, @monthly
	VersionTypeAll       VersionType = "all"       // @all (full time series)
	VersionTypeCustom    VersionType = "custom"    // Source-specific version identifier
)

// Backward compatibility alias
var VersionTypeTenor = VersionTypeLookback

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
	Path         *MonikerPath
	Namespace    *string
	Version      *string
	VersionType  *VersionType
	SubResource  *string
	Revision     *int
	Params       QueryParams
}

// String returns the canonical moniker string
func (m *Moniker) String() string {
	var parts []string

	// Namespace prefix
	if m.Namespace != nil {
		parts = append(parts, *m.Namespace+"@")
	}

	// Path
	parts = append(parts, m.Path.String())

	// Version suffix
	if m.Version != nil {
		parts = append(parts, "@"+*m.Version)
	}

	// Sub-resource (after version, before revision)
	if m.SubResource != nil {
		parts = append(parts, "/"+*m.SubResource)
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

// Domain returns the data domain (first path segment)
func (m *Moniker) Domain() *string {
	return m.Path.Domain()
}

// CanonicalPath returns the path as a string (without namespace, version, or params)
func (m *Moniker) CanonicalPath() string {
	return m.Path.String()
}

// FullPath returns path including version, sub-resource, and revision but not namespace
func (m *Moniker) FullPath() string {
	parts := []string{m.Path.String()}
	if m.Version != nil {
		parts = append(parts, "@"+*m.Version)
	}
	if m.SubResource != nil {
		parts = append(parts, "/"+*m.SubResource)
	}
	if m.Revision != nil {
		parts = append(parts, fmt.Sprintf("/v%d", *m.Revision))
	}
	return strings.Join(parts, "")
}

// IsVersioned returns true if the moniker has a version specifier
func (m *Moniker) IsVersioned() bool {
	return m.Version != nil
}

// IsLatest returns true if the moniker explicitly requests latest version
func (m *Moniker) IsLatest() bool {
	return m.Version != nil && *m.Version == "latest"
}

// VersionDate extracts date from version if it's a date format (YYYYMMDD)
func (m *Moniker) VersionDate() *string {
	if m.VersionType != nil && *m.VersionType == VersionTypeDate {
		return m.Version
	}
	// Fallback for backwards compatibility
	if m.Version != nil && len(*m.Version) == 8 {
		// Check if all digits
		matched, _ := regexp.MatchString(`^\d{8}$`, *m.Version)
		if matched {
			return m.Version
		}
	}
	return nil
}

// VersionLookback extracts lookback components if version is a lookback period
// Returns (value, unit) where unit is Y/M/W/D, or nil if not a lookback
func (m *Moniker) VersionLookback() (value *int, unit *string) {
	if m.VersionType != nil && *m.VersionType == VersionTypeLookback && m.Version != nil {
		re := regexp.MustCompile(`^(\d+)([YMWD])$`)
		matches := re.FindStringSubmatch(strings.ToUpper(*m.Version))
		if len(matches) == 3 {
			var val int
			fmt.Sscanf(matches[1], "%d", &val)
			unitStr := matches[2]
			return &val, &unitStr
		}
	}
	return nil, nil
}

// VersionTenor is a backward compatibility alias for VersionLookback
func (m *Moniker) VersionTenor() (value *int, unit *string) {
	return m.VersionLookback()
}

// VersionFrequency extracts frequency if version is a frequency specifier
// Returns frequency string (daily, weekly, monthly) or nil
func (m *Moniker) VersionFrequency() *string {
	if m.VersionType != nil && *m.VersionType == VersionTypeFrequency && m.Version != nil {
		freq := strings.ToLower(*m.Version)
		return &freq
	}
	return nil
}

// IsAll returns true if the moniker requests the full time series
func (m *Moniker) IsAll() bool {
	return m.VersionType != nil && *m.VersionType == VersionTypeAll
}

// WithVersion creates a copy with a different version
func (m *Moniker) WithVersion(version string, versionType *VersionType) *Moniker {
	return &Moniker{
		Path:        m.Path,
		Namespace:   m.Namespace,
		Version:     &version,
		VersionType: versionType,
		SubResource: m.SubResource,
		Revision:    m.Revision,
		Params:      m.Params,
	}
}

// WithNamespace creates a copy with a different namespace
func (m *Moniker) WithNamespace(namespace *string) *Moniker {
	return &Moniker{
		Path:        m.Path,
		Namespace:   namespace,
		Version:     m.Version,
		VersionType: m.VersionType,
		SubResource: m.SubResource,
		Revision:    m.Revision,
		Params:      m.Params,
	}
}

// WithSubResource creates a copy with a different sub-resource
func (m *Moniker) WithSubResource(subResource *string) *Moniker {
	return &Moniker{
		Path:        m.Path,
		Namespace:   m.Namespace,
		Version:     m.Version,
		VersionType: m.VersionType,
		SubResource: subResource,
		Revision:    m.Revision,
		Params:      m.Params,
	}
}
