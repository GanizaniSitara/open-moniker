/**
 * Shared utilities for Moniker Service UIs
 */

const MonikerUtils = {
    /**
     * Extract domain from a moniker path.
     * Domain is explicitly set on the node, or derived from the first path segment.
     * @param {Object|null} node - Node object with optional domain property
     * @param {string} path - The moniker path (e.g., "analytics.risk/var")
     * @returns {string} The domain name (e.g., "analytics")
     */
    getDomain(node, path) {
        return node?.domain || path.split(/[./]/)[0];
    },

    /**
     * Build a set of domain names that belong to a given category.
     * @param {Array} domains - Array of domain objects with name and data_category
     * @param {string} category - The category to filter by
     * @returns {Set} Set of domain names in the category
     */
    getDomainsInCategory(domains, category) {
        const allowed = new Set();
        domains.forEach(d => {
            if ((d.data_category || 'Uncategorized') === category) {
                allowed.add(d.name);
            }
        });
        return allowed;
    },

    /**
     * Build category map from domains.
     * @param {Array} domains - Array of domain objects
     * @returns {Map} Map of category -> [domain names]
     */
    buildCategoryMap(domains) {
        const categories = new Map();
        domains.forEach(d => {
            const cat = d.data_category || 'Uncategorized';
            if (!categories.has(cat)) categories.set(cat, []);
            categories.get(cat).push(d.name);
        });
        return categories;
    },

    /**
     * Render category filter chips HTML.
     * @param {Map} categories - Map of category -> [domain names]
     * @param {string} onClickFn - Name of the onclick function
     * @returns {string} HTML string for category chips
     */
    renderCategoryChips(categories, onClickFn = 'filterByCategory') {
        let html = `<span class="category-chip all active" onclick="${onClickFn}(null)">All</span>`;
        [...categories.keys()].sort().forEach(cat => {
            html += `<span class="category-chip" onclick="${onClickFn}('${cat}')">${cat}</span>`;
        });
        return html;
    },

    /**
     * Update category chip active states.
     * @param {string|null} activeCategory - Currently active category
     */
    updateCategoryChipStyles(activeCategory) {
        document.querySelectorAll('.category-chip').forEach(chip => {
            chip.classList.remove('active');
            if (activeCategory === null && chip.classList.contains('all')) {
                chip.classList.add('active');
            } else if (chip.textContent === activeCategory) {
                chip.classList.add('active');
            }
        });
    }
};

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MonikerUtils;
}
