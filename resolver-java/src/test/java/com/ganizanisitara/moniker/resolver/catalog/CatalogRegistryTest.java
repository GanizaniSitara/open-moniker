package com.ganizanisitara.moniker.resolver.catalog;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for CatalogRegistry.
 */
class CatalogRegistryTest {

    private CatalogRegistry registry;

    @BeforeEach
    void setUp() {
        registry = new CatalogRegistry();
    }

    // --- Helper to build a minimal CatalogNode ---

    private CatalogNode makeNode(String path, NodeStatus status, boolean isLeaf) {
        CatalogNode node = new CatalogNode();
        node.setPath(path);
        node.setDisplayName(path.substring(path.lastIndexOf('/') + 1));
        node.setDescription("Description for " + path);
        node.setStatus(status);
        node.setLeaf(isLeaf);
        return node;
    }

    private CatalogNode makeActiveLeaf(String path) {
        return makeNode(path, NodeStatus.ACTIVE, true);
    }

    private CatalogNode makeActiveCategory(String path) {
        return makeNode(path, NodeStatus.ACTIVE, false);
    }

    // ---- register and get ----

    @Test
    void registerAndGet() {
        CatalogNode node = makeActiveLeaf("prices.equity/AAPL");
        registry.register(node);

        CatalogNode retrieved = registry.get("prices.equity/AAPL");
        assertNotNull(retrieved);
        assertEquals("prices.equity/AAPL", retrieved.getPath());
        assertEquals("AAPL", retrieved.getDisplayName());
    }

    // ---- get nonexistent returns null ----

    @Test
    void getNonexistentReturnsNull() {
        assertNull(registry.get("does/not/exist"));
    }

    // ---- exists true / false ----

    @Test
    void existsReturnsTrueForRegistered() {
        registry.register(makeActiveLeaf("prices.equity/MSFT"));
        assertTrue(registry.exists("prices.equity/MSFT"));
    }

    @Test
    void existsReturnsFalseForUnregistered() {
        assertFalse(registry.exists("prices.equity/UNKNOWN"));
    }

    // ---- getOrVirtual ----

    @Test
    void getOrVirtualReturnsRegisteredNode() {
        CatalogNode node = makeActiveLeaf("ref/USD");
        registry.register(node);

        CatalogNode result = registry.getOrVirtual("ref/USD");
        assertSame(node, result);
    }

    @Test
    void getOrVirtualReturnsVirtualForMissing() {
        CatalogNode virtual = registry.getOrVirtual("missing/path");
        assertNotNull(virtual);
        assertEquals("missing/path", virtual.getPath());
        assertFalse(virtual.isLeaf());
        assertEquals(NodeStatus.DRAFT, virtual.getStatus());
        // Virtual node should NOT be added to the registry
        assertFalse(registry.exists("missing/path"));
    }

    // ---- childrenPaths ----

    @Test
    void childrenPathsForParent() {
        registry.register(makeActiveCategory("prices"));
        registry.register(makeActiveLeaf("prices/equity"));
        registry.register(makeActiveLeaf("prices/fx"));

        List<String> children = registry.childrenPaths("prices");
        assertEquals(2, children.size());
        assertTrue(children.contains("prices/equity"));
        assertTrue(children.contains("prices/fx"));
    }

    @Test
    void childrenPathsForUnknownParentReturnsEmpty() {
        List<String> children = registry.childrenPaths("nonexistent");
        assertNotNull(children);
        assertTrue(children.isEmpty());
    }

    // ---- children (nodes) ----

    @Test
    void childrenReturnsNodeObjects() {
        registry.register(makeActiveCategory("domain"));
        registry.register(makeActiveLeaf("domain/child1"));
        registry.register(makeActiveLeaf("domain/child2"));

        List<CatalogNode> kids = registry.children("domain");
        assertEquals(2, kids.size());
        assertTrue(kids.stream().anyMatch(n -> "domain/child1".equals(n.getPath())));
        assertTrue(kids.stream().anyMatch(n -> "domain/child2".equals(n.getPath())));
    }

    // ---- ownership resolution with inheritance ----

    @Test
    void resolveOwnershipInheritsFromAncestors() {
        CatalogNode parent = makeActiveCategory("org");
        Ownership parentOwnership = new Ownership();
        parentOwnership.setAccountableOwner("parent-owner");
        parentOwnership.setSupportChannel("#parent-support");
        parent.setOwnership(parentOwnership);
        registry.register(parent);

        CatalogNode child = makeActiveLeaf("org/team");
        Ownership childOwnership = new Ownership();
        childOwnership.setDataSpecialist("child-specialist");
        child.setOwnership(childOwnership);
        registry.register(child);

        ResolvedOwnership resolved = registry.resolveOwnership("org/team");
        // accountableOwner inherited from parent
        assertEquals("parent-owner", resolved.getAccountableOwner());
        assertEquals("org", resolved.getAccountableOwnerSource());
        // dataSpecialist set at child level
        assertEquals("child-specialist", resolved.getDataSpecialist());
        assertEquals("org/team", resolved.getDataSpecialistSource());
        // supportChannel inherited from parent
        assertEquals("#parent-support", resolved.getSupportChannel());
        assertEquals("org", resolved.getSupportChannelSource());
    }

    @Test
    void resolveOwnershipChildOverridesParent() {
        CatalogNode parent = makeActiveCategory("org");
        Ownership parentOwnership = new Ownership();
        parentOwnership.setAccountableOwner("parent-owner");
        parent.setOwnership(parentOwnership);
        registry.register(parent);

        CatalogNode child = makeActiveLeaf("org/team");
        Ownership childOwnership = new Ownership();
        childOwnership.setAccountableOwner("child-owner");
        child.setOwnership(childOwnership);
        registry.register(child);

        ResolvedOwnership resolved = registry.resolveOwnership("org/team");
        assertEquals("child-owner", resolved.getAccountableOwner());
        assertEquals("org/team", resolved.getAccountableOwnerSource());
    }

    // ---- findSourceBinding walks hierarchy ----

    @Test
    void findSourceBindingOnCurrentNode() {
        CatalogNode node = makeActiveLeaf("data/feed");
        SourceBinding binding = new SourceBinding();
        binding.setType(SourceType.SNOWFLAKE);
        node.setSourceBinding(binding);
        registry.register(node);

        CatalogNode found = registry.findSourceBinding("data/feed");
        assertNotNull(found);
        assertEquals("data/feed", found.getPath());
    }

    @Test
    void findSourceBindingWalksUpHierarchy() {
        // Parent has a source binding, child does not
        CatalogNode parent = makeActiveCategory("data");
        SourceBinding binding = new SourceBinding();
        binding.setType(SourceType.REST);
        parent.setSourceBinding(binding);
        registry.register(parent);

        CatalogNode child = makeActiveLeaf("data/sub");
        // child has no source binding, but is resolvable
        registry.register(child);

        // findSourceBinding on child path should walk up to parent
        CatalogNode found = registry.findSourceBinding("data/sub");
        assertNotNull(found);
        assertEquals("data", found.getPath());
    }

    @Test
    void findSourceBindingSkipsNonResolvableNodes() {
        // A draft node with binding should be skipped
        CatalogNode draftNode = makeNode("draft", NodeStatus.DRAFT, true);
        SourceBinding binding = new SourceBinding();
        binding.setType(SourceType.STATIC);
        draftNode.setSourceBinding(binding);
        registry.register(draftNode);

        CatalogNode found = registry.findSourceBinding("draft");
        assertNull(found);
    }

    @Test
    void findSourceBindingReturnsNullWhenNoneFound() {
        registry.register(makeActiveLeaf("noBinding/leaf"));
        assertNull(registry.findSourceBinding("noBinding/leaf"));
    }

    // ---- getAllNodes ----

    @Test
    void getAllNodesReturnsAllRegistered() {
        registry.register(makeActiveLeaf("a"));
        registry.register(makeActiveLeaf("b"));
        registry.register(makeActiveLeaf("c"));

        List<CatalogNode> all = registry.getAllNodes();
        assertEquals(3, all.size());
    }

    // ---- size ----

    @Test
    void sizeIsAccurate() {
        assertEquals(0, registry.size());

        registry.register(makeActiveLeaf("one"));
        assertEquals(1, registry.size());

        registry.register(makeActiveLeaf("two"));
        assertEquals(2, registry.size());

        registry.register(makeActiveLeaf("three"));
        assertEquals(3, registry.size());
    }

    // ---- registerMany ----

    @Test
    void registerManyRegistersAllNodes() {
        List<CatalogNode> nodes = Arrays.asList(
                makeActiveLeaf("batch/a"),
                makeActiveLeaf("batch/b"),
                makeActiveLeaf("batch/c")
        );

        registry.registerMany(nodes);

        assertEquals(3, registry.size());
        assertNotNull(registry.get("batch/a"));
        assertNotNull(registry.get("batch/b"));
        assertNotNull(registry.get("batch/c"));
    }

    @Test
    void registerManyUpdatesParentChildren() {
        registry.register(makeActiveCategory("batch"));
        registry.registerMany(Arrays.asList(
                makeActiveLeaf("batch/x"),
                makeActiveLeaf("batch/y")
        ));

        List<String> children = registry.childrenPaths("batch");
        assertEquals(2, children.size());
        assertTrue(children.contains("batch/x"));
        assertTrue(children.contains("batch/y"));
    }

    // ---- clear ----

    @Test
    void clearRemovesAllNodes() {
        registry.register(makeActiveLeaf("clearMe/a"));
        registry.register(makeActiveLeaf("clearMe/b"));
        assertEquals(2, registry.size());

        registry.clear();

        assertEquals(0, registry.size());
        assertNull(registry.get("clearMe/a"));
        assertTrue(registry.childrenPaths("clearMe").isEmpty());
    }
}
