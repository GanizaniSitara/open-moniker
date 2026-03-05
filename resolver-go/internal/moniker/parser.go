package moniker

import (
	"fmt"
	"net/url"
	"regexp"
	"strconv"
	"strings"
)

// MonikerParseError is raised when a moniker string cannot be parsed
type MonikerParseError struct {
	Message string
}

func (e *MonikerParseError) Error() string {
	return e.Message
}

// Valid segment pattern: alphanumeric, hyphens, underscores, dots
// Must start with alphanumeric
var segmentPattern = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9_.\-]*$`)

// Namespace pattern: alphanumeric, hyphens, underscores (no dots - those are for paths)
var namespacePattern = regexp.MustCompile(`^[a-zA-Z][a-zA-Z0-9_\-]*$`)

// Version pattern: digits (date) or alphanumeric (like "latest")
var versionPattern = regexp.MustCompile(`^[a-zA-Z0-9]+$`)

// Revision pattern: /vN or /VN where N is a positive integer (case-insensitive)
var revisionPattern = regexp.MustCompile(`^[vV](\d+)$`)

// Version classification patterns
var dateVersionPattern = regexp.MustCompile(`^\d{8}$`)                     // 20260101 (YYYYMMDD)
var lookbackVersionPattern = regexp.MustCompile(`^(?i)\d+[YMWD]$`)        // 3M, 12Y, 1W, 5D
var frequencyVersionPattern = regexp.MustCompile(`^(?i)(daily|weekly|monthly)$`)
var keywordVersionPattern = regexp.MustCompile(`^(?i)(latest|all)$`)

// Backward compatibility alias
var tenorVersionPattern = lookbackVersionPattern

// ClassifyVersion determines the semantic type of a version string
func ClassifyVersion(version string) *VersionType {
	if version == "" {
		return nil
	}
	if dateVersionPattern.MatchString(version) {
		vt := VersionTypeDate
		return &vt
	}
	if lookbackVersionPattern.MatchString(version) {
		vt := VersionTypeLookback
		return &vt
	}
	if frequencyVersionPattern.MatchString(version) {
		vt := VersionTypeFrequency
		return &vt
	}
	if keywordVersionPattern.MatchString(version) {
		versionLower := strings.ToLower(version)
		if versionLower == "latest" {
			vt := VersionTypeLatest
			return &vt
		} else if versionLower == "all" {
			vt := VersionTypeAll
			return &vt
		}
	}
	vt := VersionTypeCustom
	return &vt
}

// ValidateSegment checks if a path segment is valid
func ValidateSegment(segment string) bool {
	if segment == "" {
		return false
	}
	if len(segment) > 128 {
		return false
	}
	return segmentPattern.MatchString(segment)
}

// ValidateNamespace checks if a namespace is valid
func ValidateNamespace(namespace string) bool {
	if namespace == "" {
		return false
	}
	if len(namespace) > 64 {
		return false
	}
	return namespacePattern.MatchString(namespace)
}

// ParsePath parses a path string into a MonikerPath
func ParsePath(pathStr string, validate bool) (*MonikerPath, error) {
	if pathStr == "" || pathStr == "/" {
		return RootPath(), nil
	}

	// Strip leading/trailing slashes
	clean := strings.Trim(pathStr, "/")
	if clean == "" {
		return RootPath(), nil
	}

	segments := strings.Split(clean, "/")

	if validate {
		for _, seg := range segments {
			if !ValidateSegment(seg) {
				return nil, &MonikerParseError{
					Message: fmt.Sprintf("Invalid path segment: '%s'. "+
						"Segments must start with alphanumeric and contain only "+
						"alphanumerics, hyphens, underscores, or dots.", seg),
				}
			}
		}
	}

	return &MonikerPath{Segments: segments}, nil
}

// Parse parses a full moniker string
//
// Format: [namespace@]path/segments[@version][/sub.resource][/vN][?query=params]
//
// Examples:
//   - indices.sovereign/developed/EUR/ALL
//   - commodities.derivatives/crypto/ETH@20260115/v2
//   - verified@reference.security/ISIN/US0378331005@latest
//   - user@analytics.risk/views/my-watchlist@20260115/v3
//   - securities/012345678@20260101/details
//   - securities/012345678@20260101/details.corporate.actions
//   - prices.equity/AAPL@3M (3-month lookback)
//   - risk.cvar/portfolio-123@all (full time series)
//   - moniker://holdings/20260115/fund_alpha?format=json
func Parse(monikerStr string, validate bool) (*Moniker, error) {
	if monikerStr == "" {
		return nil, &MonikerParseError{Message: "Empty moniker string"}
	}

	monikerStr = strings.TrimSpace(monikerStr)

	var body string
	var queryStr string

	// Handle scheme
	if strings.HasPrefix(monikerStr, "moniker://") {
		// Parse as URL
		parsed, err := url.Parse(monikerStr)
		if err != nil {
			return nil, &MonikerParseError{Message: fmt.Sprintf("Invalid URL: %v", err)}
		}
		body = parsed.Host + parsed.Path
		queryStr = parsed.RawQuery
	} else if strings.Contains(monikerStr, "://") {
		return nil, &MonikerParseError{
			Message: fmt.Sprintf("Invalid scheme. Expected 'moniker://' or no scheme, got: %s", monikerStr),
		}
	} else {
		// No scheme - check for query string
		if strings.Contains(monikerStr, "?") {
			parts := strings.SplitN(monikerStr, "?", 2)
			body = parts[0]
			queryStr = parts[1]
		} else {
			body = monikerStr
			queryStr = ""
		}
	}

	// Parse namespace (prefix before first @, but only if @ appears before first /)
	var namespace *string
	remaining := body

	// Check for namespace@ prefix
	// The @ must appear before any / to be a namespace (otherwise it's a version)
	firstAt := strings.Index(body, "@")
	firstSlash := strings.Index(body, "/")

	if firstAt != -1 && (firstSlash == -1 || firstAt < firstSlash) {
		// This @ is a namespace prefix
		ns := body[:firstAt]
		namespace = &ns
		remaining = body[firstAt+1:]

		if validate && !ValidateNamespace(*namespace) {
			return nil, &MonikerParseError{
				Message: fmt.Sprintf("Invalid namespace: '%s'. "+
					"Namespace must start with a letter and contain only "+
					"alphanumerics, hyphens, or underscores.", *namespace),
			}
		}
	}

	// Parse revision suffix (/vN or /VN at the end - case-insensitive)
	var revision *int
	remainingLower := strings.ToLower(remaining)
	if strings.Contains(remainingLower, "/v") {
		// Find the last /v or /V pattern
		lowerIdx := strings.LastIndex(remainingLower, "/v")
		if lowerIdx != -1 {
			before := remaining[:lowerIdx]
			after := remaining[lowerIdx+2:] // Skip the "/v" or "/V"
			// Check if it's a valid revision (just digits at the end or before ?)
			revMatch := regexp.MustCompile(`^(\d+)(?:$|(?=\?))`).FindStringSubmatch(after)
			if len(revMatch) > 1 {
				rev, _ := strconv.Atoi(revMatch[1])
				revision = &rev
				remaining = before
			}
		}
	}

	// Parse version suffix with optional sub-resource: @version[/sub.resource]
	var version *string
	var subResource *string
	if strings.Contains(remaining, "@") {
		// Find the @ that's a version (not a namespace prefix)
		firstSlashInRemaining := strings.Index(remaining, "/")
		atIdx := strings.LastIndex(remaining, "@")

		// Check if this @ is after the first slash (making it a version, not namespace)
		// If no slash in remaining, check if we already parsed namespace
		isVersionAt := false
		if namespace != nil {
			// Namespace already extracted, any @ is a version
			isVersionAt = atIdx != -1
		} else {
			// No namespace yet - @ is version only if after first /
			isVersionAt = atIdx != -1 && (firstSlashInRemaining == -1 || atIdx > firstSlashInRemaining)
		}

		if isVersionAt && atIdx != -1 {
			// Everything before @ is the path
			pathPart := remaining[:atIdx]
			afterAt := remaining[atIdx+1:]

			// Check if there's a sub-resource (path after version)
			// Pattern: @version/sub.resource or just @version
			if strings.Contains(afterAt, "/") {
				parts := strings.SplitN(afterAt, "/", 2)
				ver := parts[0]
				sub := parts[1]
				version = &ver
				subResource = &sub
			} else {
				version = &afterAt
			}

			remaining = pathPart

			if validate && version != nil && !versionPattern.MatchString(*version) {
				return nil, &MonikerParseError{
					Message: fmt.Sprintf("Invalid version: '%s'. "+
						"Version must be alphanumeric (e.g., 'latest', '20260115', '3M').", *version),
				}
			}

			// Validate sub_resource segments if present
			if validate && subResource != nil {
				// Sub-resource uses dots for multi-level: details.corporate.actions
				// Each dot-separated part should be a valid segment
				for _, part := range strings.Split(*subResource, ".") {
					if !ValidateSegment(part) {
						return nil, &MonikerParseError{
							Message: fmt.Sprintf("Invalid sub-resource segment: '%s'. "+
								"Sub-resource parts must start with alphanumeric.", part),
						}
					}
				}
			}
		}
	}

	// Parse path
	path, err := ParsePath(remaining, validate)
	if err != nil {
		return nil, err
	}

	// Parse query params
	params := make(QueryParams)
	if queryStr != "" {
		parsedQS, err := url.ParseQuery(queryStr)
		if err == nil {
			// Take first value for each param (no multi-value support)
			for key, values := range parsedQS {
				if len(values) > 0 {
					params[key] = values[0]
				}
			}
		}
	}

	// Classify version type
	var versionType *VersionType
	if version != nil {
		versionType = ClassifyVersion(*version)
	}

	return &Moniker{
		Path:        path,
		Namespace:   namespace,
		Version:     version,
		VersionType: versionType,
		SubResource: subResource,
		Revision:    revision,
		Params:      params,
	}, nil
}

// ParseMoniker is a convenience wrapper around Parse with validation enabled
func ParseMoniker(monikerStr string) (*Moniker, error) {
	return Parse(monikerStr, true)
}

// NormalizeMoniker normalizes a moniker string to canonical form
// Always returns: moniker://[namespace@]path[@version][/vN][?sorted_params]
func NormalizeMoniker(monikerStr string) (string, error) {
	m, err := ParseMoniker(monikerStr)
	if err != nil {
		return "", err
	}
	return m.String(), nil
}

// BuildMoniker builds a Moniker from components
func BuildMoniker(pathStr string, namespace *string, version *string, versionType *VersionType,
	subResource *string, revision *int, params QueryParams) (*Moniker, error) {

	path, err := ParsePath(pathStr, true)
	if err != nil {
		return nil, err
	}

	// Auto-classify version if not explicitly provided
	effectiveVersionType := versionType
	if effectiveVersionType == nil && version != nil {
		effectiveVersionType = ClassifyVersion(*version)
	}

	if params == nil {
		params = make(QueryParams)
	}

	return &Moniker{
		Path:        path,
		Namespace:   namespace,
		Version:     version,
		VersionType: effectiveVersionType,
		SubResource: subResource,
		Revision:    revision,
		Params:      params,
	}, nil
}
