package com.ganizanisitara.moniker.resolver.moniker;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Represents a complete moniker reference.
 *
 * Format: [namespace@]path/segments[/vN][?query=params]
 *
 * The @ character within a path segment denotes an identity parameter:
 *     holdings/positions@ACC001/summary
 */
public class Moniker {
    private final MonikerPath path;
    private final String namespace;
    private final int[] segmentId; // {index} or null
    private final String segmentIdValue; // the identity value after @
    private final String dateParam; // date@VALUE: "20260101", "latest", "3M", etc.
    private final String filterShortlink; // filter@CODE that was expanded
    private final Integer revision;
    private final QueryParams params;

    public Moniker(MonikerPath path, String namespace, int[] segmentIdIndex,
                   String segmentIdValue, String dateParam, String filterShortlink,
                   Integer revision, QueryParams params) {
        this.path = path;
        this.namespace = namespace;
        this.segmentId = segmentIdIndex;
        this.segmentIdValue = segmentIdValue;
        this.dateParam = dateParam;
        this.filterShortlink = filterShortlink;
        this.revision = revision;
        this.params = params != null ? params : new QueryParams();
    }

    /**
     * Convenience constructor without segment ID, date, or filter.
     */
    public Moniker(MonikerPath path, String namespace, Integer revision, QueryParams params) {
        this(path, namespace, null, null, null, null, revision, params);
    }

    /**
     * Return the path string with @id re-injected into the correct segment.
     */
    private String pathWithSegmentId() {
        String pathStr = path.toString();
        if (segmentId == null) {
            return pathStr;
        }
        List<String> segments = new ArrayList<>(path.getSegments());
        int idx = segmentId[0];
        if (idx < segments.size()) {
            segments.set(idx, segments.get(idx) + "@" + segmentIdValue);
        }
        return String.join("/", segments);
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();

        // Namespace prefix
        if (namespace != null) {
            sb.append(namespace).append("@");
        }

        // Path (with @id re-injected)
        sb.append(pathWithSegmentId());

        // Date segment (before revision)
        if (dateParam != null) {
            sb.append("/date@").append(dateParam);
        }

        // Revision suffix
        if (revision != null) {
            sb.append("/v").append(revision);
        }

        String base = sb.toString();

        // Query params
        if (!params.isEmpty()) {
            List<String> paramParts = new ArrayList<>();
            for (Map.Entry<String, String> entry : params.asMap().entrySet()) {
                paramParts.add(entry.getKey() + "=" + entry.getValue());
            }
            return "moniker://" + base + "?" + String.join("&", paramParts);
        }

        return "moniker://" + base;
    }

    /**
     * Get the data domain (first path segment).
     */
    public String domain() {
        return path.domain();
    }

    /**
     * Get the clean path for catalog lookup (without @id, namespace, or params).
     */
    public String canonicalPath() {
        return path.toString();
    }

    /**
     * Get full path including @id and revision but not namespace.
     */
    public String fullPath() {
        StringBuilder sb = new StringBuilder(pathWithSegmentId());
        if (revision != null) {
            sb.append("/v").append(revision);
        }
        return sb.toString();
    }

    /**
     * Check if the moniker has a segment identity parameter.
     */
    public boolean hasSegmentId() {
        return segmentId != null;
    }

    /**
     * Get the segment identity index, or -1 if none.
     */
    public int getSegmentIdIndex() {
        return segmentId != null ? segmentId[0] : -1;
    }

    /**
     * Get the segment identity value, or null if none.
     */
    public String getSegmentIdValue() {
        return segmentIdValue;
    }

    /**
     * Create a copy with a different namespace.
     */
    public Moniker withNamespace(String namespace) {
        return new Moniker(path, namespace, segmentId, segmentIdValue, dateParam, filterShortlink, revision, params);
    }

    // Getters
    public MonikerPath getPath() {
        return path;
    }

    public String getNamespace() {
        return namespace;
    }

    public String getDateParam() {
        return dateParam;
    }

    public String getFilterShortlink() {
        return filterShortlink;
    }

    public Integer getRevision() {
        return revision;
    }

    public QueryParams getParams() {
        return params;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Moniker moniker = (Moniker) o;
        return Objects.equals(path, moniker.path) &&
                Objects.equals(namespace, moniker.namespace) &&
                Objects.equals(segmentIdValue, moniker.segmentIdValue) &&
                Objects.equals(revision, moniker.revision);
    }

    @Override
    public int hashCode() {
        return Objects.hash(path, namespace, segmentIdValue, revision);
    }
}
