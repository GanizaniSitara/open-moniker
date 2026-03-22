package moniker

import (
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

func TestParseWithLookbackVersion(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL@3M")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Version == nil || *m.Version != "3M" {
		t.Errorf("expected version '3M', got %v", m.Version)
	}
	if m.VersionType == nil || *m.VersionType != VersionTypeLookback {
		t.Errorf("expected version type lookback, got %v", m.VersionType)
	}
}

func TestParseWithDateVersion(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL@20260101")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Version == nil || *m.Version != "20260101" {
		t.Errorf("expected version '20260101', got %v", m.Version)
	}
	if m.VersionType == nil || *m.VersionType != VersionTypeDate {
		t.Errorf("expected version type date, got %v", m.VersionType)
	}
}

func TestParseWithLatestVersion(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL@latest")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Version == nil || *m.Version != "latest" {
		t.Errorf("expected version 'latest', got %v", m.Version)
	}
	if m.VersionType == nil || *m.VersionType != VersionTypeLatest {
		t.Errorf("expected version type latest, got %v", m.VersionType)
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
	m, err := ParseMoniker("prices/AAPL@latest/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Version == nil || *m.Version != "latest" {
		t.Errorf("expected version 'latest', got %v", m.Version)
	}
	if m.Revision == nil || *m.Revision != 2 {
		t.Errorf("expected revision 2, got %v", m.Revision)
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

func TestParseWithSubResource(t *testing.T) {
	m, err := ParseMoniker("securities/012345678@20260101/details")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.SubResource == nil || *m.SubResource != "details" {
		t.Errorf("expected sub_resource 'details', got %v", m.SubResource)
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

func TestParseWithNamespaceAndVersion(t *testing.T) {
	m, err := ParseMoniker("verified@reference.security/ISIN/US0378331005@latest")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Namespace == nil || *m.Namespace != "verified" {
		t.Errorf("expected namespace 'verified', got %v", m.Namespace)
	}
	if m.Version == nil || *m.Version != "latest" {
		t.Errorf("expected version 'latest', got %v", m.Version)
	}
	expectedPath := "reference.security/ISIN/US0378331005"
	if m.Path.String() != expectedPath {
		t.Errorf("expected path %q, got %q", expectedPath, m.Path.String())
	}
}

func TestParseWithAllVersion(t *testing.T) {
	m, err := ParseMoniker("risk.cvar/portfolio-123@all")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.VersionType == nil || *m.VersionType != VersionTypeAll {
		t.Errorf("expected version type ALL, got %v", m.VersionType)
	}
}

func TestParseFrequencyVersion(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL@daily")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.VersionType == nil || *m.VersionType != VersionTypeFrequency {
		t.Errorf("expected version type frequency, got %v", m.VersionType)
	}
}

func TestParseNoValidation(t *testing.T) {
	// Parse without validation should accept anything
	m, err := Parse("some/path", false)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.Path.String() != "some/path" {
		t.Errorf("expected path 'some/path', got %q", m.Path.String())
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

// --- ClassifyVersion tests ---

func TestClassifyVersionLookback(t *testing.T) {
	vt := ClassifyVersion("3M")
	if vt == nil || *vt != VersionTypeLookback {
		t.Errorf("expected lookback, got %v", vt)
	}
}

func TestClassifyVersionDate(t *testing.T) {
	vt := ClassifyVersion("20260101")
	if vt == nil || *vt != VersionTypeDate {
		t.Errorf("expected date, got %v", vt)
	}
}

func TestClassifyVersionLatest(t *testing.T) {
	vt := ClassifyVersion("latest")
	if vt == nil || *vt != VersionTypeLatest {
		t.Errorf("expected latest, got %v", vt)
	}
}

func TestClassifyVersionDaily(t *testing.T) {
	vt := ClassifyVersion("daily")
	if vt == nil || *vt != VersionTypeFrequency {
		t.Errorf("expected frequency, got %v", vt)
	}
}

func TestClassifyVersionAll(t *testing.T) {
	vt := ClassifyVersion("all")
	if vt == nil || *vt != VersionTypeAll {
		t.Errorf("expected all, got %v", vt)
	}
}

func TestClassifyVersionCustom(t *testing.T) {
	vt := ClassifyVersion("custom")
	if vt == nil || *vt != VersionTypeCustom {
		t.Errorf("expected custom, got %v", vt)
	}
}

func TestClassifyVersionEmpty(t *testing.T) {
	vt := ClassifyVersion("")
	if vt != nil {
		t.Errorf("expected nil for empty version, got %v", vt)
	}
}

func TestClassifyVersionWeekly(t *testing.T) {
	vt := ClassifyVersion("weekly")
	if vt == nil || *vt != VersionTypeFrequency {
		t.Errorf("expected frequency, got %v", vt)
	}
}

func TestClassifyVersionMonthly(t *testing.T) {
	vt := ClassifyVersion("monthly")
	if vt == nil || *vt != VersionTypeFrequency {
		t.Errorf("expected frequency, got %v", vt)
	}
}

func TestClassifyVersionLookbackYear(t *testing.T) {
	vt := ClassifyVersion("12Y")
	if vt == nil || *vt != VersionTypeLookback {
		t.Errorf("expected lookback, got %v", vt)
	}
}

func TestClassifyVersionLookbackWeek(t *testing.T) {
	vt := ClassifyVersion("1W")
	if vt == nil || *vt != VersionTypeLookback {
		t.Errorf("expected lookback, got %v", vt)
	}
}

func TestClassifyVersionLookbackDay(t *testing.T) {
	vt := ClassifyVersion("5D")
	if vt == nil || *vt != VersionTypeLookback {
		t.Errorf("expected lookback, got %v", vt)
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

func TestNormalizeMonikerWithVersion(t *testing.T) {
	result, err := NormalizeMoniker("prices/AAPL@latest")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expected := "moniker://prices/AAPL@latest"
	if result != expected {
		t.Errorf("expected %q, got %q", expected, result)
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
	m, err := ParseMoniker("prod@prices/AAPL@latest/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m.CanonicalPath() != "prices/AAPL" {
		t.Errorf("expected canonical path 'prices/AAPL', got %q", m.CanonicalPath())
	}
}

func TestMonikerFullPath(t *testing.T) {
	m, err := ParseMoniker("prices/AAPL@latest/v2")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	expected := "prices/AAPL@latest/v2"
	if m.FullPath() != expected {
		t.Errorf("expected full path %q, got %q", expected, m.FullPath())
	}
}

func TestMonikerIsVersioned(t *testing.T) {
	m, _ := ParseMoniker("prices/AAPL@latest")
	if !m.IsVersioned() {
		t.Error("expected IsVersioned to be true")
	}
	m2, _ := ParseMoniker("prices/AAPL")
	if m2.IsVersioned() {
		t.Error("expected IsVersioned to be false")
	}
}

func TestMonikerIsLatest(t *testing.T) {
	m, _ := ParseMoniker("prices/AAPL@latest")
	if !m.IsLatest() {
		t.Error("expected IsLatest to be true")
	}
	m2, _ := ParseMoniker("prices/AAPL@20260101")
	if m2.IsLatest() {
		t.Error("expected IsLatest to be false for date version")
	}
}

func TestMonikerDomain(t *testing.T) {
	m, _ := ParseMoniker("prices/AAPL@latest")
	d := m.Domain()
	if d == nil || *d != "prices" {
		t.Errorf("expected domain 'prices', got %v", d)
	}
}

func TestMonikerVersionLookback(t *testing.T) {
	m, _ := ParseMoniker("prices/AAPL@3M")
	val, unit := m.VersionLookback()
	if val == nil || *val != 3 {
		t.Errorf("expected lookback value 3, got %v", val)
	}
	if unit == nil || *unit != "M" {
		t.Errorf("expected lookback unit 'M', got %v", unit)
	}
}

func TestMonikerVersionDate(t *testing.T) {
	m, _ := ParseMoniker("prices/AAPL@20260101")
	d := m.VersionDate()
	if d == nil || *d != "20260101" {
		t.Errorf("expected version date '20260101', got %v", d)
	}
}

func TestMonikerVersionFrequency(t *testing.T) {
	m, _ := ParseMoniker("prices/AAPL@daily")
	f := m.VersionFrequency()
	if f == nil || *f != "daily" {
		t.Errorf("expected frequency 'daily', got %v", f)
	}
}

func TestMonikerIsAll(t *testing.T) {
	m, _ := ParseMoniker("risk.cvar/portfolio-123@all")
	if !m.IsAll() {
		t.Error("expected IsAll to be true")
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
