package catalog

import (
	"sort"
	"testing"
)

func strPtr(s string) *string {
	return &s
}

func makeNode(path, displayName, description string, status NodeStatus, isLeaf bool) *CatalogNode {
	return &CatalogNode{
		Path:        path,
		DisplayName: displayName,
		Description: description,
		Status:      status,
		IsLeaf:      isLeaf,
	}
}

// --- Register and Get ---

func TestRegisterAndGet(t *testing.T) {
	r := NewRegistry()
	node := makeNode("prices/equity", "Equity Prices", "equity prices data", NodeStatusActive, true)
	r.Register(node)

	got := r.Get("prices/equity")
	if got == nil {
		t.Fatal("expected node, got nil")
	}
	if got.Path != "prices/equity" {
		t.Errorf("expected path 'prices/equity', got %q", got.Path)
	}
	if got.DisplayName != "Equity Prices" {
		t.Errorf("expected display name 'Equity Prices', got %q", got.DisplayName)
	}
}

func TestGetNonExistent(t *testing.T) {
	r := NewRegistry()
	got := r.Get("nonexistent")
	if got != nil {
		t.Errorf("expected nil, got %v", got)
	}
}

// --- Exists ---

func TestExistsTrue(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices/equity", "Equity", "", NodeStatusActive, true))
	if !r.Exists("prices/equity") {
		t.Error("expected Exists to return true")
	}
}

func TestExistsFalse(t *testing.T) {
	r := NewRegistry()
	if r.Exists("nonexistent") {
		t.Error("expected Exists to return false")
	}
}

// --- ChildrenPaths ---

func TestChildrenPaths(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))
	r.Register(makeNode("prices/equity", "Equity", "", NodeStatusActive, true))
	r.Register(makeNode("prices/fx", "FX", "", NodeStatusActive, true))

	paths := r.ChildrenPaths("prices")
	sort.Strings(paths)

	if len(paths) != 2 {
		t.Fatalf("expected 2 children, got %d", len(paths))
	}
	if paths[0] != "prices/equity" {
		t.Errorf("expected 'prices/equity', got %q", paths[0])
	}
	if paths[1] != "prices/fx" {
		t.Errorf("expected 'prices/fx', got %q", paths[1])
	}
}

func TestChildrenPathsEmpty(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))

	paths := r.ChildrenPaths("prices")
	if len(paths) != 0 {
		t.Errorf("expected 0 children, got %d", len(paths))
	}
}

// --- Children ---

func TestChildren(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))
	r.Register(makeNode("prices/equity", "Equity", "", NodeStatusActive, true))
	r.Register(makeNode("prices/fx", "FX", "", NodeStatusActive, true))

	children := r.Children("prices")
	if len(children) != 2 {
		t.Fatalf("expected 2 children, got %d", len(children))
	}

	paths := make([]string, len(children))
	for i, c := range children {
		paths[i] = c.Path
	}
	sort.Strings(paths)
	if paths[0] != "prices/equity" || paths[1] != "prices/fx" {
		t.Errorf("unexpected children paths: %v", paths)
	}
}

// --- Ownership resolution with inheritance ---

func TestResolveOwnershipDirect(t *testing.T) {
	r := NewRegistry()
	node := makeNode("prices/equity", "Equity", "", NodeStatusActive, true)
	node.Ownership = &Ownership{
		AccountableOwner: strPtr("alice"),
		DataSpecialist:   strPtr("bob"),
	}
	r.Register(node)

	resolved := r.ResolveOwnership("prices/equity")
	if resolved.AccountableOwner == nil || *resolved.AccountableOwner != "alice" {
		t.Errorf("expected accountable owner 'alice', got %v", resolved.AccountableOwner)
	}
	if resolved.DataSpecialist == nil || *resolved.DataSpecialist != "bob" {
		t.Errorf("expected data specialist 'bob', got %v", resolved.DataSpecialist)
	}
}

func TestResolveOwnershipInheritance(t *testing.T) {
	r := NewRegistry()

	parent := makeNode("prices", "Prices", "", NodeStatusActive, false)
	parent.Ownership = &Ownership{
		AccountableOwner: strPtr("parent-owner"),
		SupportChannel:   strPtr("#prices-support"),
	}
	r.Register(parent)

	child := makeNode("prices/equity", "Equity", "", NodeStatusActive, true)
	child.Ownership = &Ownership{
		DataSpecialist: strPtr("child-specialist"),
	}
	r.Register(child)

	resolved := r.ResolveOwnership("prices/equity")

	// AccountableOwner inherited from parent
	if resolved.AccountableOwner == nil || *resolved.AccountableOwner != "parent-owner" {
		t.Errorf("expected inherited accountable owner 'parent-owner', got %v", resolved.AccountableOwner)
	}
	// DataSpecialist from child
	if resolved.DataSpecialist == nil || *resolved.DataSpecialist != "child-specialist" {
		t.Errorf("expected data specialist 'child-specialist', got %v", resolved.DataSpecialist)
	}
	// SupportChannel inherited from parent
	if resolved.SupportChannel == nil || *resolved.SupportChannel != "#prices-support" {
		t.Errorf("expected support channel '#prices-support', got %v", resolved.SupportChannel)
	}
}

func TestResolveOwnershipChildOverridesParent(t *testing.T) {
	r := NewRegistry()

	parent := makeNode("prices", "Prices", "", NodeStatusActive, false)
	parent.Ownership = &Ownership{
		AccountableOwner: strPtr("parent-owner"),
	}
	r.Register(parent)

	child := makeNode("prices/equity", "Equity", "", NodeStatusActive, true)
	child.Ownership = &Ownership{
		AccountableOwner: strPtr("child-owner"),
	}
	r.Register(child)

	resolved := r.ResolveOwnership("prices/equity")
	if resolved.AccountableOwner == nil || *resolved.AccountableOwner != "child-owner" {
		t.Errorf("expected child to override parent, got %v", resolved.AccountableOwner)
	}
}

func TestResolveOwnershipNoOwnership(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))

	resolved := r.ResolveOwnership("prices")
	if resolved.AccountableOwner != nil {
		t.Errorf("expected nil accountable owner, got %v", resolved.AccountableOwner)
	}
}

// --- FindSourceBinding ---

func TestFindSourceBindingDirect(t *testing.T) {
	r := NewRegistry()
	node := makeNode("prices/equity", "Equity", "", NodeStatusActive, true)
	node.SourceBinding = &SourceBinding{
		SourceType: SourceTypeSnowflake,
		Config:     map[string]interface{}{"table": "equity_prices"},
	}
	r.Register(node)

	binding, path := r.FindSourceBinding("prices/equity")
	if binding == nil {
		t.Fatal("expected binding, got nil")
	}
	if binding.SourceType != SourceTypeSnowflake {
		t.Errorf("expected snowflake, got %v", binding.SourceType)
	}
	if path != "prices/equity" {
		t.Errorf("expected binding path 'prices/equity', got %q", path)
	}
}

func TestFindSourceBindingInherited(t *testing.T) {
	r := NewRegistry()

	parent := makeNode("prices", "Prices", "", NodeStatusActive, false)
	parent.SourceBinding = &SourceBinding{
		SourceType: SourceTypeOracle,
		Config:     map[string]interface{}{"dsn": "oracle://localhost"},
	}
	r.Register(parent)

	r.Register(makeNode("prices/equity", "Equity", "", NodeStatusActive, true))

	binding, path := r.FindSourceBinding("prices/equity")
	if binding == nil {
		t.Fatal("expected inherited binding, got nil")
	}
	if binding.SourceType != SourceTypeOracle {
		t.Errorf("expected oracle, got %v", binding.SourceType)
	}
	if path != "prices" {
		t.Errorf("expected binding path 'prices', got %q", path)
	}
}

func TestFindSourceBindingNone(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))

	binding, path := r.FindSourceBinding("prices")
	if binding != nil {
		t.Errorf("expected nil binding, got %v", binding)
	}
	if path != "" {
		t.Errorf("expected empty path, got %q", path)
	}
}

func TestFindSourceBindingSkipsDraft(t *testing.T) {
	r := NewRegistry()

	parent := makeNode("prices", "Prices", "", NodeStatusActive, false)
	parent.SourceBinding = &SourceBinding{
		SourceType: SourceTypeOracle,
		Config:     map[string]interface{}{},
	}
	r.Register(parent)

	child := makeNode("prices/equity", "Equity", "", NodeStatusDraft, true)
	child.SourceBinding = &SourceBinding{
		SourceType: SourceTypeSnowflake,
		Config:     map[string]interface{}{},
	}
	r.Register(child)

	// Draft node's binding should be skipped, inheriting from parent
	binding, path := r.FindSourceBinding("prices/equity")
	if binding == nil {
		t.Fatal("expected binding from parent, got nil")
	}
	if path != "prices" {
		t.Errorf("expected binding from 'prices' (parent), got %q", path)
	}
}

// --- AllPaths ---

func TestAllPaths(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))
	r.Register(makeNode("risk", "Risk", "", NodeStatusActive, false))

	paths := r.AllPaths()
	sort.Strings(paths)

	if len(paths) != 2 {
		t.Fatalf("expected 2 paths, got %d", len(paths))
	}
	if paths[0] != "prices" || paths[1] != "risk" {
		t.Errorf("unexpected paths: %v", paths)
	}
}

// --- Search ---

func TestSearchByPath(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices/equity", "Equity Prices", "Stock prices", NodeStatusActive, true))
	r.Register(makeNode("risk/cvar", "CVaR", "credit risk", NodeStatusActive, true))

	results := r.Search("equity", nil, 10)
	if len(results) == 0 {
		t.Fatal("expected at least 1 search result")
	}
	found := false
	for _, n := range results {
		if n.Path == "prices/equity" {
			found = true
		}
	}
	if !found {
		t.Error("expected 'prices/equity' in search results")
	}
}

func TestSearchByDescription(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("risk/cvar", "CVaR", "Conditional Value at Risk metrics", NodeStatusActive, true))

	results := r.Search("conditional", nil, 10)
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
}

func TestSearchByTag(t *testing.T) {
	r := NewRegistry()
	node := makeNode("prices/equity", "Equity", "desc", NodeStatusActive, true)
	node.Tags = []string{"market-data", "equities"}
	r.Register(node)

	results := r.Search("equities", nil, 10)
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
}

func TestSearchWithStatusFilter(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices/equity", "Equity", "", NodeStatusActive, true))
	r.Register(makeNode("prices/deprecated", "Old", "", NodeStatusDeprecated, true))

	status := NodeStatusActive
	results := r.Search("prices", &status, 10)
	for _, n := range results {
		if n.Status != NodeStatusActive {
			t.Errorf("expected only active results, got status %q", n.Status)
		}
	}
}

func TestSearchLimitHonored(t *testing.T) {
	r := NewRegistry()
	for i := 0; i < 20; i++ {
		r.Register(makeNode("prices/item"+string(rune('A'+i)), "Item", "test desc", NodeStatusActive, true))
	}

	results := r.Search("item", nil, 5)
	if len(results) > 5 {
		t.Errorf("expected at most 5 results, got %d", len(results))
	}
}

// --- Count ---

func TestCount(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("a", "A", "", NodeStatusActive, true))
	r.Register(makeNode("b", "B", "", NodeStatusActive, true))
	r.Register(makeNode("c", "C", "", NodeStatusDeprecated, true))

	counts := r.Count()
	if counts["total"] != 3 {
		t.Errorf("expected total=3, got %d", counts["total"])
	}
	if counts[string(NodeStatusActive)] != 2 {
		t.Errorf("expected active=2, got %d", counts[string(NodeStatusActive)])
	}
	if counts[string(NodeStatusDeprecated)] != 1 {
		t.Errorf("expected deprecated=1, got %d", counts[string(NodeStatusDeprecated)])
	}
}

// --- Clear ---

func TestClear(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))
	r.Register(makeNode("risk", "Risk", "", NodeStatusActive, false))

	r.Clear()

	if len(r.AllPaths()) != 0 {
		t.Errorf("expected 0 paths after clear, got %d", len(r.AllPaths()))
	}
	if r.Exists("prices") {
		t.Error("expected 'prices' not to exist after clear")
	}
}

// --- AtomicReplace ---

func TestAtomicReplace(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("old/path", "Old", "", NodeStatusActive, true))

	newNodes := []*CatalogNode{
		makeNode("new/path1", "New1", "", NodeStatusActive, true),
		makeNode("new/path2", "New2", "", NodeStatusActive, true),
	}
	r.AtomicReplace(newNodes)

	if r.Exists("old/path") {
		t.Error("expected old node to be removed after AtomicReplace")
	}
	if !r.Exists("new/path1") {
		t.Error("expected 'new/path1' to exist")
	}
	if !r.Exists("new/path2") {
		t.Error("expected 'new/path2' to exist")
	}

	// Children should be rebuilt
	children := r.ChildrenPaths("new")
	sort.Strings(children)
	if len(children) != 2 {
		t.Fatalf("expected 2 children of 'new', got %d", len(children))
	}
}

// --- RegisterMany ---

func TestRegisterMany(t *testing.T) {
	r := NewRegistry()
	nodes := []*CatalogNode{
		makeNode("a", "A", "", NodeStatusActive, false),
		makeNode("b", "B", "", NodeStatusActive, false),
		makeNode("c", "C", "", NodeStatusActive, false),
	}
	r.RegisterMany(nodes)

	if len(r.AllPaths()) != 3 {
		t.Errorf("expected 3 paths, got %d", len(r.AllPaths()))
	}
}

// --- GetOrVirtual ---

func TestGetOrVirtualExisting(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("prices", "Prices", "", NodeStatusActive, false))

	node := r.GetOrVirtual("prices")
	if node.DisplayName != "Prices" {
		t.Errorf("expected 'Prices', got %q", node.DisplayName)
	}
}

func TestGetOrVirtualNonExisting(t *testing.T) {
	r := NewRegistry()
	node := r.GetOrVirtual("nonexistent")
	if node == nil {
		t.Fatal("expected virtual node, got nil")
	}
	if node.Path != "nonexistent" {
		t.Errorf("expected path 'nonexistent', got %q", node.Path)
	}
	if node.IsLeaf {
		t.Error("expected virtual node to not be leaf")
	}
}

// --- FindByStatus ---

func TestFindByStatus(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("a", "A", "", NodeStatusActive, true))
	r.Register(makeNode("b", "B", "", NodeStatusDeprecated, true))
	r.Register(makeNode("c", "C", "", NodeStatusActive, true))

	active := r.FindByStatus(NodeStatusActive)
	if len(active) != 2 {
		t.Errorf("expected 2 active, got %d", len(active))
	}

	deprecated := r.FindByStatus(NodeStatusDeprecated)
	if len(deprecated) != 1 {
		t.Errorf("expected 1 deprecated, got %d", len(deprecated))
	}
}

// --- Dot-separated hierarchy ---

func TestDotSeparatedHierarchy(t *testing.T) {
	r := NewRegistry()
	r.Register(makeNode("analytics", "Analytics", "", NodeStatusActive, false))
	r.Register(makeNode("analytics.risk", "Risk Analytics", "", NodeStatusActive, false))
	r.Register(makeNode("analytics.risk/var", "VaR", "", NodeStatusActive, true))

	// analytics.risk should be a child of analytics
	children := r.ChildrenPaths("analytics")
	if len(children) != 1 || children[0] != "analytics.risk" {
		t.Errorf("expected child 'analytics.risk', got %v", children)
	}

	// analytics.risk/var should be a child of analytics.risk
	children2 := r.ChildrenPaths("analytics.risk")
	if len(children2) != 1 || children2[0] != "analytics.risk/var" {
		t.Errorf("expected child 'analytics.risk/var', got %v", children2)
	}
}
