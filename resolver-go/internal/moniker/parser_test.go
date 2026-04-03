package moniker

import (
	"strings"
	"testing"
)

// --- ParseMoniker / Parse tests ---

func TestParseSimplePath(t *testing.T) {
	m, err := ParseMoniker("risk.cvar")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(m.Path.Segments) != 1 {
		t.Fatalf("expected 1 segment, got %d", len(m.Path.Segments))
	}
	if m.Path.Segments[0] != "risk.cvar" {
		t.Errorf("expected segment 'risk.cvar', got %q", m.Path.Segments[0])
	}
}

func TestParseMultiSegment(t *testing.T) {
	m, err := ParseMoniker("fixed.income/govies/treasury")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expected := []string{"fixed.income", "govies", "treasury"}
	if len(m.Path.Segments) != len(expected) {
		t.Fatalf("expected %d segments, got %d", len(expected), len(m.Path.Segments))
	}
	for i, seg := range expected {
		if m.Path.Segments[i] != seg {
			t.Errorf("segment[%d]: expected %q, got %q", i, seg, m.Path.Segments[i])
		}
	}
}

func TestParseWithNamespace(t *testing.T) {
	m, err := ParseMoniker("prod@prices/AAPL")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Namespace == nil || *m.Namespace != "prod" {
		t.Errorf("expected namespace 'prod', got %v", m.Namespace)
	}
	if m.Path.String() != "prices/AAPL" {
		t.Errorf("expected path 'prices/AAPL', got %q", m.Path.String())
	}
}

func TestParseWithRevision(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Revision == nil || *m.Revision != 2 {
		t.Errorf("expected revision 2, got %v", m.Revision)
	}
	if m.Path.String() != "prices/AAPL" {
		t.Errorf("expected path 'prices/AAPL', got %q", m.Path.String())
	}
}

func TestParseWithScheme(t *testing.T) {
	m, err := ParseMoniker("moniker://risk.cvar")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(m.Path.Segments) != 1 || m.Path.Segments[0] != "risk.cvar" {
		t.Errorf("expected path 'risk.cvar', got %v", m.Path.Segments)
	}
}

func TestParseWithQueryParams(t *testing.T) {
	m, err := ParseMoniker("holdings/fund_alpha?format=json&limit=100")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if v, ok := m.Params["format"]; !ok || v != "json" {
		t.Errorf("expected param format=json, got %v", m.Params)
	}
	if v, ok := m.Params["limit"]; !ok || v != "100" {
		t.Errorf("expected param limit=100, got %v", m.Params)
	}
}

func TestParseEmptyString(t *testing.T) {
	_, err := ParseMoniker("")
	if err == nil {
		t.Fatal("expected error for empty moniker string")
	}
}

func TestParseInvalidScheme(t *testing.T) {
	_, err := ParseMoniker("http://risk.cvar")
	if err == nil {
		t.Fatal("expected error for invalid scheme")
	}
}

func TestParseNoValidation(t *testing.T) {
	m, err := Parse("some/path", false)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Path.String() != "some/path" {
		t.Errorf("expected path 'some/path', got %q", m.Path.String())
	}
}

func TestParseWithNamespaceAndRevision(t *testing.T) {
	m, err := ParseMoniker("prod@prices/AAPL/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Namespace == nil || *m.Namespace != "prod" {
		t.Errorf("expected namespace 'prod', got %v", m.Namespace)
	}
	if m.Revision == nil || *m.Revision != 2 {
		t.Errorf("expected revision 2, got %v", m.Revision)
	}
	if m.Path.String() != "prices/AAPL" {
		t.Errorf("expected path 'prices/AAPL', got %q", m.Path.String())
	}
}

// --- @id identity parameter tests (OM-17) ---

func TestParseSegmentIdMidPath(t *testing.T) {
	m, err := ParseMoniker("holdings/positions@ACC001/summary")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.SegmentID == nil {
		t.Fatal("expected segment_id to be set")
	}
	if m.SegmentID.Index != 1 {
		t.Errorf("expected segment_id index 1, got %d", m.SegmentID.Index)
	}
	if m.SegmentID.Value != "ACC001" {
		t.Errorf("expected segment_id value 'ACC001', got %q", m.SegmentID.Value)
	}
	// canonical_path must be clean (no @id)
	if m.CanonicalPath() != "holdings/positions/summary" {
		t.Errorf("expected canonical_path 'holdings/positions/summary', got %q", m.CanonicalPath())
	}
}

func TestParseSegmentIdFirstSegment(t *testing.T) {
	// Segment 0 @id requires namespace prefix to avoid ambiguity
	m, err := ParseMoniker("prod@portfolios@FUND_ALPHA/holdings")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Namespace == nil || *m.Namespace != "prod" {
		t.Errorf("expected namespace 'prod', got %v", m.Namespace)
	}
	if m.SegmentID == nil {
		t.Fatal("expected segment_id to be set")
	}
	if m.SegmentID.Index != 0 {
		t.Errorf("expected segment_id index 0, got %d", m.SegmentID.Index)
	}
	if m.SegmentID.Value != "FUND_ALPHA" {
		t.Errorf("expected segment_id value 'FUND_ALPHA', got %q", m.SegmentID.Value)
	}
	if m.CanonicalPath() != "portfolios/holdings" {
		t.Errorf("expected canonical_path 'portfolios/holdings', got %q", m.CanonicalPath())
	}
}

func TestParseSegmentIdWithRevision(t *testing.T) {
	m, err := ParseMoniker("holdings/positions@ACC001/summary/v3")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.SegmentID == nil || m.SegmentID.Value != "ACC001" {
		t.Fatalf("expected segment_id ACC001, got %v", m.SegmentID)
	}
	if m.Revision == nil || *m.Revision != 3 {
		t.Errorf("expected revision 3, got %v", m.Revision)
	}
	if m.CanonicalPath() != "holdings/positions/summary" {
		t.Errorf("expected canonical_path 'holdings/positions/summary', got %q", m.CanonicalPath())
	}
}

func TestParseSegmentIdWithNamespace(t *testing.T) {
	m, err := ParseMoniker("prod@holdings/positions@ACC001/summary")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Namespace == nil || *m.Namespace != "prod" {
		t.Errorf("expected namespace 'prod', got %v", m.Namespace)
	}
	if m.SegmentID == nil || m.SegmentID.Value != "ACC001" {
		t.Fatalf("expected segment_id ACC001, got %v", m.SegmentID)
	}
	if m.CanonicalPath() != "holdings/positions/summary" {
		t.Errorf("expected canonical_path 'holdings/positions/summary', got %q", m.CanonicalPath())
	}
}

func TestParseNoSegmentId(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.SegmentID != nil {
		t.Errorf("expected segment_id to be nil, got %v", m.SegmentID)
	}
}

func TestParseSegmentIdFullPath(t *testing.T) {
	m, err := ParseMoniker("holdings/positions@ACC001/summary")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expected := "holdings/positions@ACC001/summary"
	if m.FullPath() != expected {
		t.Errorf("expected full_path %q, got %q", expected, m.FullPath())
	}
}

func TestParseSegmentIdStringRoundtrip(t *testing.T) {
	m, err := ParseMoniker("holdings/positions@ACC001/summary")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	s := m.String()
	if !strings.Contains(s, "positions@ACC001") {
		t.Errorf("expected String() to contain 'positions@ACC001', got %q", s)
	}
}

func TestParseSegmentIdSpecialChars(t *testing.T) {
	m, err := ParseMoniker("holdings/positions@ACC-001.test_val/summary")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.SegmentID == nil || m.SegmentID.Value != "ACC-001.test_val" {
		t.Errorf("expected segment_id value 'ACC-001.test_val', got %v", m.SegmentID)
	}
}

// --- @id error cases ---

func TestParseSegmentIdAtEndOfPathReject(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL@20260101")
	if err == nil {
		t.Fatal("expected error for @ at end of path")
	}
	if !strings.Contains(err.Error(), "Invalid use of '@' at end of path") {
		t.Errorf("unexpected error message: %v", err)
	}
}

func TestParseSegmentIdMultipleReject(t *testing.T) {
	// Use namespace prefix so that the first @ isn't consumed as namespace
	_, err := ParseMoniker("ns@holdings@ACC001/positions@XYZ/summary")
	if err == nil {
		t.Fatal("expected error for multiple @id parameters")
	}
	if !strings.Contains(err.Error(), "At most one @id") {
		t.Errorf("unexpected error message: %v", err)
	}
}

func TestParseSegmentIdEmptyReject(t *testing.T) {
	_, err := ParseMoniker("holdings/positions@/summary")
	if err == nil {
		t.Fatal("expected error for empty @id value")
	}
	if !strings.Contains(err.Error(), "Empty @id value") {
		t.Errorf("unexpected error message: %v", err)
	}
}

func TestParseSegmentIdInvalidCharsReject(t *testing.T) {
	_, err := ParseMoniker("holdings/positions@ACC 001/summary")
	if err == nil {
		t.Fatal("expected error for invalid @id characters")
	}
	if !strings.Contains(err.Error(), "Invalid segment identity value") {
		t.Errorf("unexpected error message: %v", err)
	}
}

// --- @version rejection tests (OM-19: @version syntax removed) ---

func TestRejectAtVersionLatest(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL@latest")
	if err == nil {
		t.Fatal("expected error: @version syntax is removed")
	}
}

func TestRejectAtVersionDate(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL@20260101")
	if err == nil {
		t.Fatal("expected error: @version syntax is removed")
	}
}

func TestRejectAtVersionLookback(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL@3M")
	if err == nil {
		t.Fatal("expected error: @version syntax is removed")
	}
}

func TestRejectAtVersionAll(t *testing.T) {
	_, err := ParseMoniker("risk.cvar/portfolio-123@all")
	if err == nil {
		t.Fatal("expected error: @version syntax is removed")
	}
}

func TestRejectAtVersionFrequency(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL@daily")
	if err == nil {
		t.Fatal("expected error: @version syntax is removed")
	}
}

func TestRejectBareAtEnd(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL@")
	if err == nil {
		t.Fatal("expected error: bare @ at end of path")
	}
}

// --- date@VALUE tests (OM-20) ---

func TestParseDateParamAbsolute(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL/date@20260101")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "20260101" {
		t.Errorf("expected date_param '20260101', got %v", m.DateParam)
	}
	if m.CanonicalPath() != "prices/equity/AAPL" {
		t.Errorf("expected canonical_path without date@, got %q", m.CanonicalPath())
	}
}

func TestParseDateParamLatest(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL/date@latest")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "latest" {
		t.Errorf("expected date_param 'latest', got %v", m.DateParam)
	}
}

func TestParseDateParamPrevious(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL/date@previous")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "previous" {
		t.Errorf("expected date_param 'previous', got %v", m.DateParam)
	}
}

func TestParseDateParamRelative(t *testing.T) {
	cases := []string{"3M", "1Y", "2W", "5D"}
	for _, val := range cases {
		m, err := ParseMoniker("prices/equity/AAPL/date@" + val)
		if err != nil {
			t.Fatalf("date@%s: unexpected error: %v", val, err)
		}
		if m.DateParam == nil || *m.DateParam != val {
			t.Errorf("date@%s: expected date_param %q, got %v", val, val, m.DateParam)
		}
	}
}

func TestParseDateParamNotInCanonicalPath(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL/date@20260101")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if strings.Contains(m.CanonicalPath(), "date@") {
		t.Errorf("canonical_path must not contain date@, got %q", m.CanonicalPath())
	}
	// date@ is not a positional segment
	if len(m.Path.Segments) != 3 {
		t.Errorf("expected 3 segments (no date@), got %d", len(m.Path.Segments))
	}
}

func TestParseDateParamWithSegmentId(t *testing.T) {
	m, err := ParseMoniker("holdings/positions@ACC001/summary/date@20260101")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.SegmentID == nil || m.SegmentID.Value != "ACC001" {
		t.Errorf("expected segment_id ACC001, got %v", m.SegmentID)
	}
	if m.DateParam == nil || *m.DateParam != "20260101" {
		t.Errorf("expected date_param '20260101', got %v", m.DateParam)
	}
}

func TestParseDateParamWithRevision(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL/date@20260101/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "20260101" {
		t.Errorf("expected date_param '20260101', got %v", m.DateParam)
	}
	if m.Revision == nil || *m.Revision != 2 {
		t.Errorf("expected revision 2, got %v", m.Revision)
	}
}

func TestParseDateParamWithQueryParams(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL/date@latest?format=json")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "latest" {
		t.Errorf("expected date_param 'latest', got %v", m.DateParam)
	}
	if v, ok := m.Params["format"]; !ok || v != "json" {
		t.Errorf("expected param format=json, got %v", m.Params)
	}
}

func TestParseDateParamInStringOutput(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL/date@20260101")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	s := m.String()
	if !strings.Contains(s, "date@20260101") {
		t.Errorf("expected String() to contain 'date@20260101', got %q", s)
	}
}

func TestParseDateParamCaseInsensitive(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL/date@Latest")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "Latest" {
		t.Errorf("expected date_param 'Latest', got %v", m.DateParam)
	}
}

func TestParseDateParamEmpty(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL/date@")
	if err == nil {
		t.Fatal("expected error for empty date@")
	}
}

func TestParseDateParamInvalid(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL/date@notadate")
	if err == nil {
		t.Fatal("expected error for invalid date@ value")
	}
}

func TestParseDateParamZeroPrefix(t *testing.T) {
	_, err := ParseMoniker("prices/AAPL/date@0M")
	if err == nil {
		t.Fatal("expected error for date@0M (must start with 1-9)")
	}
}

func TestParseDateParamWithScheme(t *testing.T) {
	m, err := ParseMoniker("moniker://prices/equity/AAPL/date@20260101")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "20260101" {
		t.Errorf("expected date_param '20260101', got %v", m.DateParam)
	}
}

func TestParseNoDateParamByDefault(t *testing.T) {
	m, err := ParseMoniker("prices/equity/AAPL")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam != nil {
		t.Errorf("expected date_param nil, got %v", m.DateParam)
	}
}

func TestParseDateParamWithNamespace(t *testing.T) {
	m, err := ParseMoniker("prod@prices/equity/AAPL/date@20260101")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Namespace == nil || *m.Namespace != "prod" {
		t.Errorf("expected namespace 'prod', got %v", m.Namespace)
	}
	if m.DateParam == nil || *m.DateParam != "20260101" {
		t.Errorf("expected date_param '20260101', got %v", m.DateParam)
	}
}

// --- filter@CODE tests (OM-21) ---

// mockStore implements ShortlinkStore for testing
type mockStore struct {
	entries map[string]*ShortlinkEntry
}

func (s *mockStore) Get(code string) *ShortlinkEntry {
	return s.entries[code]
}

func newMockStore() *mockStore {
	return &mockStore{
		entries: map[string]*ShortlinkEntry{
			"abc123": {
				FilterSegments: []string{"developed", "EUR"},
				Params:         map[string]string{"region": "EMEA"},
			},
		},
	}
}

func TestParseFilterExpands(t *testing.T) {
	store := newMockStore()
	m, err := ParseMonikerWithStore("prices/equity/filter@abc123", store)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.FilterShortlink == nil || *m.FilterShortlink != "filter@abc123" {
		t.Errorf("expected filter_shortlink 'filter@abc123', got %v", m.FilterShortlink)
	}
	// Path should contain expanded segments
	if m.CanonicalPath() != "prices/equity/developed/EUR" {
		t.Errorf("expected expanded path 'prices/equity/developed/EUR', got %q", m.CanonicalPath())
	}
	// Params should include shortlink params
	if v, ok := m.Params["region"]; !ok || v != "EMEA" {
		t.Errorf("expected param region=EMEA, got %v", m.Params)
	}
}

func TestParseFilterSplicesInPlace(t *testing.T) {
	store := newMockStore()
	m, err := ParseMonikerWithStore("prices/equity/filter@abc123/summary", store)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.CanonicalPath() != "prices/equity/developed/EUR/summary" {
		t.Errorf("expected 'prices/equity/developed/EUR/summary', got %q", m.CanonicalPath())
	}
}

func TestParseFilterWithSegmentId(t *testing.T) {
	store := newMockStore()
	m, err := ParseMonikerWithStore("holdings/positions@ACC001/filter@abc123/summary", store)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.SegmentID == nil || m.SegmentID.Value != "ACC001" {
		t.Errorf("expected segment_id ACC001, got %v", m.SegmentID)
	}
	if m.FilterShortlink == nil {
		t.Error("expected filter_shortlink to be set")
	}
}

func TestParseFilterWithDateParam(t *testing.T) {
	store := newMockStore()
	m, err := ParseMonikerWithStore("prices/equity/filter@abc123/date@20260101", store)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.DateParam == nil || *m.DateParam != "20260101" {
		t.Errorf("expected date_param '20260101', got %v", m.DateParam)
	}
}

func TestParseFilterEmptyCode(t *testing.T) {
	_, err := ParseMoniker("prices/equity/filter@")
	if err == nil {
		t.Fatal("expected error for empty filter@ code")
	}
}

func TestParseFilterNoStore(t *testing.T) {
	_, err := ParseMoniker("prices/equity/filter@abc123")
	if err == nil {
		t.Fatal("expected error for filter@ without store")
	}
}

func TestParseFilterUnknownCode(t *testing.T) {
	store := newMockStore()
	_, err := ParseMonikerWithStore("prices/equity/filter@UNKNOWN", store)
	if err == nil {
		t.Fatal("expected error for unknown filter@ code")
	}
}

func TestParseFilterCanonicalPathClean(t *testing.T) {
	store := newMockStore()
	m, err := ParseMonikerWithStore("prices/equity/filter@abc123", store)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if strings.Contains(m.CanonicalPath(), "filter@") {
		t.Errorf("canonical_path must not contain filter@, got %q", m.CanonicalPath())
	}
}

// --- ParsePath tests ---

func TestParsePathSimple(t *testing.T) {
	p, err := ParsePath("risk/cvar", true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(p.Segments) != 2 {
		t.Fatalf("expected 2 segments, got %d", len(p.Segments))
	}
	if p.Segments[0] != "risk" || p.Segments[1] != "cvar" {
		t.Errorf("unexpected segments: %v", p.Segments)
	}
}

func TestParsePathEmpty(t *testing.T) {
	p, err := ParsePath("", true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !p.IsEmpty() {
		t.Error("expected root (empty) path")
	}
}

func TestParsePathSlashOnly(t *testing.T) {
	p, err := ParsePath("/", true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !p.IsEmpty() {
		t.Error("expected root (empty) path for '/'")
	}
}

func TestParsePathLeadingTrailingSlashes(t *testing.T) {
	p, err := ParsePath("/prices/AAPL/", true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(p.Segments) != 2 {
		t.Fatalf("expected 2 segments, got %d", len(p.Segments))
	}
	if p.Segments[0] != "prices" || p.Segments[1] != "AAPL" {
		t.Errorf("unexpected segments: %v", p.Segments)
	}
}

func TestParsePathInvalidSegment(t *testing.T) {
	_, err := ParsePath("prices/$AAPL", true)
	if err == nil {
		t.Fatal("expected error for invalid segment '$AAPL'")
	}
}

// --- ValidateSegment tests ---

func TestValidateSegmentValid(t *testing.T) {
	valids := []string{"risk", "AAPL", "risk.cvar", "my-segment", "under_score", "a123"}
	for _, s := range valids {
		if !ValidateSegment(s) {
			t.Errorf("expected segment %q to be valid", s)
		}
	}
}

func TestValidateSegmentInvalid(t *testing.T) {
	invalids := []string{"", "$bad", " space", ".dot-start", "-dash-start", "_under-start"}
	for _, s := range invalids {
		if ValidateSegment(s) {
			t.Errorf("expected segment %q to be invalid", s)
		}
	}
}

func TestValidateSegmentTooLong(t *testing.T) {
	long := ""
	for i := 0; i < 129; i++ {
		long += "a"
	}
	if ValidateSegment(long) {
		t.Error("expected segment > 128 chars to be invalid")
	}
}

// --- ValidateNamespace tests ---

func TestValidateNamespaceValid(t *testing.T) {
	valids := []string{"prod", "staging", "my-ns", "under_score", "Dev"}
	for _, ns := range valids {
		if !ValidateNamespace(ns) {
			t.Errorf("expected namespace %q to be valid", ns)
		}
	}
}

func TestValidateNamespaceInvalid(t *testing.T) {
	invalids := []string{"", "1bad", ".dot", "-dash"}
	for _, ns := range invalids {
		if ValidateNamespace(ns) {
			t.Errorf("expected namespace %q to be invalid", ns)
		}
	}
}

func TestValidateNamespaceTooLong(t *testing.T) {
	long := "a"
	for i := 0; i < 64; i++ {
		long += "b"
	}
	if ValidateNamespace(long) {
		t.Error("expected namespace > 64 chars to be invalid")
	}
}

// --- NormalizeMoniker tests ---

func TestNormalizeMonikerSimple(t *testing.T) {
	result, err := NormalizeMoniker("risk.cvar")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "moniker://risk.cvar" {
		t.Errorf("expected 'moniker://risk.cvar', got %q", result)
	}
}

func TestNormalizeMonikerWithScheme(t *testing.T) {
	result, err := NormalizeMoniker("moniker://risk.cvar")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "moniker://risk.cvar" {
		t.Errorf("expected 'moniker://risk.cvar', got %q", result)
	}
}

func TestNormalizeMonikerWithNamespace(t *testing.T) {
	result, err := NormalizeMoniker("prod@prices/AAPL")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expected := "moniker://prod@prices/AAPL"
	if result != expected {
		t.Errorf("expected %q, got %q", expected, result)
	}
}

func TestNormalizeMonikerInvalid(t *testing.T) {
	_, err := NormalizeMoniker("")
	if err == nil {
		t.Fatal("expected error for empty string")
	}
}

// --- Moniker method tests ---

func TestMonikerCanonicalPath(t *testing.T) {
	m, err := ParseMoniker("prod@prices/AAPL/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.CanonicalPath() != "prices/AAPL" {
		t.Errorf("expected canonical path 'prices/AAPL', got %q", m.CanonicalPath())
	}
}

func TestMonikerFullPath(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expected := "prices/AAPL/v2"
	if m.FullPath() != expected {
		t.Errorf("expected full path %q, got %q", expected, m.FullPath())
	}
}

func TestMonikerDomain(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	d := m.Domain()
	if d == nil || *d != "prices" {
		t.Errorf("expected domain 'prices', got %v", d)
	}
}

// --- MonikerPath tests ---

func TestMonikerPathString(t *testing.T) {
	p := NewMonikerPath([]string{"prices", "equity", "AAPL"})
	if p.String() != "prices/equity/AAPL" {
		t.Errorf("expected 'prices/equity/AAPL', got %q", p.String())
	}
}

func TestMonikerPathLen(t *testing.T) {
	p := NewMonikerPath([]string{"a", "b", "c"})
	if p.Len() != 3 {
		t.Errorf("expected 3, got %d", p.Len())
	}
}

func TestMonikerPathParent(t *testing.T) {
	p := NewMonikerPath([]string{"a", "b", "c"})
	parent := p.Parent()
	if parent == nil || parent.String() != "a/b" {
		t.Errorf("expected parent 'a/b', got %v", parent)
	}
}

func TestMonikerPathParentAtRoot(t *testing.T) {
	p := NewMonikerPath([]string{"a"})
	parent := p.Parent()
	if parent != nil {
		t.Error("expected nil parent for single-segment path")
	}
}

func TestMonikerPathChild(t *testing.T) {
	p := NewMonikerPath([]string{"a", "b"})
	child := p.Child("c")
	if child.String() != "a/b/c" {
		t.Errorf("expected 'a/b/c', got %q", child.String())
	}
}

func TestMonikerPathIsAncestorOf(t *testing.T) {
	ancestor := NewMonikerPath([]string{"a", "b"})
	descendant := NewMonikerPath([]string{"a", "b", "c"})
	if !ancestor.IsAncestorOf(descendant) {
		t.Error("expected ancestor.IsAncestorOf(descendant) to be true")
	}
	if descendant.IsAncestorOf(ancestor) {
		t.Error("expected descendant.IsAncestorOf(ancestor) to be false")
	}
}

func TestMonikerPathIsDescendantOf(t *testing.T) {
	ancestor := NewMonikerPath([]string{"a", "b"})
	descendant := NewMonikerPath([]string{"a", "b", "c"})
	if !descendant.IsDescendantOf(ancestor) {
		t.Error("expected descendant.IsDescendantOf(ancestor) to be true")
	}
}

func TestMonikerPathLeaf(t *testing.T) {
	p := NewMonikerPath([]string{"a", "b", "c"})
	leaf := p.Leaf()
	if leaf == nil || *leaf != "c" {
		t.Errorf("expected leaf 'c', got %v", leaf)
	}
}

func TestMonikerPathAncestors(t *testing.T) {
	p := NewMonikerPath([]string{"a", "b", "c"})
	ancestors := p.Ancestors()
	if len(ancestors) != 2 {
		t.Fatalf("expected 2 ancestors, got %d", len(ancestors))
	}
	if ancestors[0].String() != "a" {
		t.Errorf("expected first ancestor 'a', got %q", ancestors[0].String())
	}
	if ancestors[1].String() != "a/b" {
		t.Errorf("expected second ancestor 'a/b', got %q", ancestors[1].String())
	}
}

func TestFromString(t *testing.T) {
	p := FromString("prices/equity/AAPL")
	if p.String() != "prices/equity/AAPL" {
		t.Errorf("expected 'prices/equity/AAPL', got %q", p.String())
	}
}

func TestFromStringEmpty(t *testing.T) {
	p := FromString("")
	if !p.IsEmpty() {
		t.Error("expected empty path for empty string")
	}
}

func TestFromStringSlash(t *testing.T) {
	p := FromString("/")
	if !p.IsEmpty() {
		t.Error("expected empty path for '/'")
	}
}
