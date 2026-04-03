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

// Segment identity value pattern: alphanumeric, hyphens, underscores, dots
var segmentIDValuePattern = regexp.MustCompile(`^[a-zA-Z0-9_.\-]+$`)

// date@VALUE patterns: absolute (YYYYMMDD), relative (3M, 1Y, 5D), symbolic (latest, previous)
var dateParamPattern = regexp.MustCompile(`(?i)^(?:\d{8}|[1-9]\d*[YMWD]|latest|previous)$`)

// filter@ prefix for shortlink expansion
const filterPrefix = "filter@"

// Revision pattern: /vN or /VN where N is a positive integer (case-insensitive)
var revisionPattern = regexp.MustCompile(`^[vV](\d+)$`)

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

// ShortlinkEntry represents an expanded shortlink
type ShortlinkEntry struct {
	FilterSegments []string
	Params         map[string]string
}

// ShortlinkStore provides shortlink lookup for filter@CODE expansion
type ShortlinkStore interface {
	Get(code string) *ShortlinkEntry
}

// Parse parses a full moniker string
//
// Format: [namespace@]path/segments[/date@VALUE][/vN][?query=params]
//
// Reserved segments:
//   - date@VALUE — date parameter (final position, not in canonical_path)
//   - filter@CODE — shortlink expansion (requires ShortlinkStore via ParseWithStore)
//   - segment@ID — identity parameter (mid-path only, at most one)
//
// Examples:
//   - indices.sovereign/developed/EUR
//   - holdings/positions@ACC001/summary
//   - prices/equity/AAPL/date@20260101
//   - prod@prices/equity/AAPL/v2
//   - moniker://holdings/fund_alpha?format=json
func Parse(monikerStr string, validate bool) (*Moniker, error) {
	return ParseWithStore(monikerStr, validate, nil)
}

// ParseWithStore parses a moniker with an optional shortlink store for filter@CODE expansion
func ParseWithStore(monikerStr string, validate bool, store ShortlinkStore) (*Moniker, error) {
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
		lowerIdx := strings.LastIndex(remainingLower, "/v")
		if lowerIdx != -1 {
			before := remaining[:lowerIdx]
			after := remaining[lowerIdx+2:] // Skip the "/v" or "/V"
			revMatch := regexp.MustCompile(`^(\d+)(?:$|\?)`).FindStringSubmatch(after)
			if len(revMatch) > 1 {
				rev, _ := strconv.Atoi(revMatch[1])
				revision = &rev
				remaining = before
			}
		}
	}

	// Expand filter@CODE segments (reserved, checked before date@ and @id).
	var filterShortlink *string
	var extraParams map[string]string
	if strings.Contains(remaining, filterPrefix) {
		parts := strings.Split(remaining, "/")
		for i, seg := range parts {
			if strings.HasPrefix(seg, filterPrefix) {
				code := seg[len(filterPrefix):]
				if code == "" {
					return nil, &MonikerParseError{Message: "Empty code in 'filter@'."}
				}
				if store == nil {
					return nil, &MonikerParseError{
						Message: fmt.Sprintf("Cannot expand '%s': no shortlink store available.", seg),
					}
				}
				link := store.Get(code)
				if link == nil {
					return nil, &MonikerParseError{
						Message: fmt.Sprintf("Shortlink not found: '%s'.", code),
					}
				}
				// Splice: replace filter@CODE with expanded filter segments
				before := parts[:i]
				after := parts[i+1:]
				newParts := make([]string, 0, len(before)+len(link.FilterSegments)+len(after))
				newParts = append(newParts, before...)
				newParts = append(newParts, link.FilterSegments...)
				newParts = append(newParts, after...)
				remaining = strings.Join(newParts, "/")
				extraParams = link.Params
				fl := fmt.Sprintf("filter@%s", code)
				filterShortlink = &fl
				break // one filter@ per path
			}
		}
	}

	// Extract date@VALUE from final segment (reserved segment).
	// "date" is a globally hard-reserved segment name. Does NOT count against @id limit.
	var dateParam *string
	if strings.Contains(remaining, "@") {
		parts := strings.Split(remaining, "/")
		final := parts[len(parts)-1]
		if strings.HasPrefix(final, "date@") {
			dateValue := final[5:] // strip "date@"
			if dateValue == "" {
				return nil, &MonikerParseError{Message: "Empty date value in 'date@'."}
			}
			if validate && !dateParamPattern.MatchString(dateValue) {
				return nil, &MonikerParseError{
					Message: fmt.Sprintf("Invalid date parameter: '%s'. "+
						"Must be YYYYMMDD, relative (e.g., 3M, 1Y, 5D), "+
						"or symbolic (latest, previous).", dateValue),
				}
			}
			dateParam = &dateValue
			// Remove the date segment from the path
			parts = parts[:len(parts)-1]
			remaining = strings.Join(parts, "/")
		}
	}

	// Extract in-path segment identity (@id embedded in a path segment).
	// @ is ONLY valid as an identity parameter within a non-final segment.
	// @ at end of path is a parse error (old @version syntax is removed).
	var segmentID *SegmentID
	if strings.Contains(remaining, "@") {
		parts := strings.Split(remaining, "/")

		// Find segments containing @
		type atSeg struct {
			idx  int
			text string
		}
		var midAt []atSeg
		var finalAt []atSeg
		for i, p := range parts {
			if strings.Contains(p, "@") {
				if i < len(parts)-1 {
					midAt = append(midAt, atSeg{i, p})
				} else {
					finalAt = append(finalAt, atSeg{i, p})
				}
			}
		}

		// @ in the final segment is a parse error (no more @version syntax)
		if len(finalAt) > 0 {
			return nil, &MonikerParseError{
				Message: fmt.Sprintf("Invalid use of '@' at end of path in '%s'. "+
					"The @ character is only valid as an identity parameter "+
					"within a mid-path segment (e.g., segment@id/rest).", finalAt[0].text),
			}
		}

		if len(midAt) > 0 {
			if len(midAt) > 1 {
				return nil, &MonikerParseError{
					Message: "At most one @id identity parameter is allowed per path.",
				}
			}

			segIdx := midAt[0].idx
			segText := midAt[0].text
			atPos := strings.Index(segText, "@")
			segName := segText[:atPos]
			segIDValue := segText[atPos+1:]

			if segIDValue == "" {
				return nil, &MonikerParseError{
					Message: fmt.Sprintf("Empty @id value in segment '%s'.", segText),
				}
			}
			if validate && !segmentIDValuePattern.MatchString(segIDValue) {
				return nil, &MonikerParseError{
					Message: fmt.Sprintf("Invalid segment identity value: '%s'. "+
						"Must contain only alphanumerics, hyphens, underscores, or dots.", segIDValue),
				}
			}

			segmentID = &SegmentID{Index: segIdx, Value: segIDValue}
			// Replace the segment with the clean name (without @id)
			parts[segIdx] = segName
			remaining = strings.Join(parts, "/")
		}
	}

	// Parse path
	path, err := ParsePath(remaining, validate)
	if err != nil {
		return nil, err
	}

	// Parse query params (shortlink params first, client params override)
	params := make(QueryParams)
	for k, v := range extraParams {
		params[k] = v
	}
	if queryStr != "" {
		parsedQS, err := url.ParseQuery(queryStr)
		if err == nil {
			for key, values := range parsedQS {
				if len(values) > 0 {
					params[key] = values[0]
				}
			}
		}
	}

	return &Moniker{
		Path:            path,
		Namespace:       namespace,
		SegmentID:       segmentID,
		DateParam:       dateParam,
		FilterShortlink: filterShortlink,
		Revision:        revision,
		Params:          params,
	}, nil
}

// ParseMoniker is a convenience wrapper around Parse with validation enabled
func ParseMoniker(monikerStr string) (*Moniker, error) {
	return ParseWithStore(monikerStr, true, nil)
}

// ParseMonikerWithStore parses with validation and an optional shortlink store
func ParseMonikerWithStore(monikerStr string, store ShortlinkStore) (*Moniker, error) {
	return ParseWithStore(monikerStr, true, store)
}

// NormalizeMoniker normalizes a moniker string to canonical form
func NormalizeMoniker(monikerStr string) (string, error) {
	m, err := ParseMoniker(monikerStr)
	if err != nil {
		return "", err
	}
	return m.String(), nil
}

// BuildMoniker builds a Moniker from components
func BuildMoniker(pathStr string, namespace *string, segmentID *SegmentID,
	dateParam *string, revision *int, params QueryParams) (*Moniker, error) {

	path, err := ParsePath(pathStr, true)
	if err != nil {
		return nil, err
	}

	if params == nil {
		params = make(QueryParams)
	}

	return &Moniker{
		Path:      path,
		Namespace: namespace,
		SegmentID: segmentID,
		DateParam: dateParam,
		Revision:  revision,
		Params:    params,
	}, nil
}
