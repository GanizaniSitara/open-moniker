package com.ganizanisitara.moniker.resolver.moniker;

import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Parser for moniker strings.
 *
 * Format: [namespace@]path/segments[/vN][?query=params]
 *
 * The @ character within a path segment denotes an identity parameter:
 *     holdings/positions@ACC001/summary
 *
 * Examples:
 *   - indices.sovereign/developed/EUR
 *   - holdings/positions@ACC001/summary
 *   - prod@prices/equity/AAPL/v2
 *   - moniker://holdings/fund_alpha?format=json
 */
public class MonikerParser {

    // Validation patterns
    private static final Pattern SEGMENT_PATTERN = Pattern.compile("^[a-zA-Z0-9][a-zA-Z0-9_.\\-]*$");
    private static final Pattern NAMESPACE_PATTERN = Pattern.compile("^[a-zA-Z][a-zA-Z0-9_\\-]*$");
    private static final Pattern SEGMENT_ID_VALUE_PATTERN = Pattern.compile("^[a-zA-Z0-9_.\\-]+$");

    // date@VALUE patterns: absolute (YYYYMMDD), relative (3M, 1Y, 5D), symbolic (latest, previous)
    private static final Pattern DATE_PARAM_PATTERN = Pattern.compile(
        "^(?:\\d{8}|[1-9]\\d*[YMWD]|latest|previous)$", Pattern.CASE_INSENSITIVE
    );

    // filter@ prefix for shortlink expansion
    private static final String FILTER_PREFIX = "filter@";

    // Max lengths
    private static final int MAX_SEGMENT_LENGTH = 128;
    private static final int MAX_NAMESPACE_LENGTH = 64;

    /**
     * Interface for shortlink lookup (used by filter@CODE expansion).
     */
    public interface ShortlinkStore {
        ShortlinkEntry get(String code);
    }

    /**
     * Represents an expanded shortlink entry.
     */
    public static class ShortlinkEntry {
        private final List<String> filterSegments;
        private final java.util.Map<String, String> params;

        public ShortlinkEntry(List<String> filterSegments, java.util.Map<String, String> params) {
            this.filterSegments = filterSegments;
            this.params = params != null ? params : new java.util.HashMap<>();
        }

        public List<String> getFilterSegments() { return filterSegments; }
        public java.util.Map<String, String> getParams() { return params; }
    }

    /**
     * Validate a path segment.
     */
    public static boolean validateSegment(String segment) {
        if (segment == null || segment.isEmpty()) {
            return false;
        }
        if (segment.length() > MAX_SEGMENT_LENGTH) {
            return false;
        }
        return SEGMENT_PATTERN.matcher(segment).matches();
    }

    /**
     * Validate a namespace.
     */
    public static boolean validateNamespace(String namespace) {
        if (namespace == null || namespace.isEmpty()) {
            return false;
        }
        if (namespace.length() > MAX_NAMESPACE_LENGTH) {
            return false;
        }
        return NAMESPACE_PATTERN.matcher(namespace).matches();
    }

    /**
     * Parse a path string into a MonikerPath.
     */
    public static MonikerPath parsePath(String pathStr, boolean validate) throws MonikerParseException {
        if (pathStr == null || pathStr.isEmpty() || pathStr.equals("/")) {
            return MonikerPath.root();
        }

        // Strip leading/trailing slashes
        String clean = pathStr.replaceAll("^/+|/+$", "");
        if (clean.isEmpty()) {
            return MonikerPath.root();
        }

        String[] segments = clean.split("/");

        if (validate) {
            for (String seg : segments) {
                if (!validateSegment(seg)) {
                    throw new MonikerParseException(
                        String.format("Invalid path segment: '%s'. Segments must start with " +
                                     "alphanumeric and contain only alphanumerics, hyphens, underscores, or dots.", seg)
                    );
                }
            }
        }

        return new MonikerPath(Arrays.asList(segments));
    }

    /**
     * Parse a full moniker string.
     */
    public static Moniker parse(String monikerStr, boolean validate) throws MonikerParseException {
        return parse(monikerStr, validate, null);
    }

    /**
     * Parse a full moniker string with an optional shortlink store.
     */
    public static Moniker parse(String monikerStr, boolean validate, ShortlinkStore store) throws MonikerParseException {
        if (monikerStr == null || monikerStr.isEmpty()) {
            throw new MonikerParseException("Empty moniker string");
        }

        monikerStr = monikerStr.trim();

        String body;
        String queryStr = null;

        // Handle scheme
        if (monikerStr.startsWith("moniker://")) {
            try {
                int queryIndex = monikerStr.indexOf('?');
                if (queryIndex != -1) {
                    body = monikerStr.substring(10, queryIndex);
                    queryStr = monikerStr.substring(queryIndex + 1);
                } else {
                    body = monikerStr.substring(10);
                }
            } catch (Exception e) {
                throw new MonikerParseException("Invalid URL: " + e.getMessage(), e);
            }
        } else if (monikerStr.contains("://")) {
            throw new MonikerParseException(
                "Invalid scheme. Expected 'moniker://' or no scheme, got: " + monikerStr
            );
        } else {
            int queryIndex = monikerStr.indexOf('?');
            if (queryIndex != -1) {
                body = monikerStr.substring(0, queryIndex);
                queryStr = monikerStr.substring(queryIndex + 1);
            } else {
                body = monikerStr;
            }
        }

        // Parse namespace (prefix before first @, but only if @ appears before first /)
        String namespace = null;
        String remaining = body;

        int firstAt = body.indexOf('@');
        int firstSlash = body.indexOf('/');

        if (firstAt != -1 && (firstSlash == -1 || firstAt < firstSlash)) {
            namespace = body.substring(0, firstAt);
            remaining = body.substring(firstAt + 1);

            if (validate && !validateNamespace(namespace)) {
                throw new MonikerParseException(
                    String.format("Invalid namespace: '%s'. Namespace must start with a letter " +
                                 "and contain only alphanumerics, hyphens, or underscores.", namespace)
                );
            }
        }

        // Parse revision suffix (/vN or /VN at the end - case-insensitive)
        Integer revision = null;
        String remainingLower = remaining.toLowerCase();
        int lastVIndex = remainingLower.lastIndexOf("/v");
        if (lastVIndex != -1) {
            String before = remaining.substring(0, lastVIndex);
            String after = remaining.substring(lastVIndex + 2);

            Pattern revPattern = Pattern.compile("^(\\d+)(?:$|(?=\\?))");
            Matcher matcher = revPattern.matcher(after);
            if (matcher.find()) {
                revision = Integer.parseInt(matcher.group(1));
                remaining = before;
            }
        }

        // Expand filter@CODE segments (reserved, checked before date@ and @id).
        String filterShortlink = null;
        java.util.Map<String, String> extraParams = new java.util.HashMap<>();
        if (remaining.contains(FILTER_PREFIX)) {
            String[] filterParts = remaining.split("/");
            for (int i = 0; i < filterParts.length; i++) {
                if (filterParts[i].startsWith(FILTER_PREFIX)) {
                    String code = filterParts[i].substring(FILTER_PREFIX.length());
                    if (code.isEmpty()) {
                        throw new MonikerParseException("Empty code in 'filter@'.");
                    }
                    if (store == null) {
                        throw new MonikerParseException(
                            String.format("Cannot expand '%s': no shortlink store available.", filterParts[i])
                        );
                    }
                    ShortlinkEntry link = store.get(code);
                    if (link == null) {
                        throw new MonikerParseException(
                            String.format("Shortlink not found: '%s'.", code)
                        );
                    }
                    // Splice: replace filter@CODE with expanded filter segments
                    List<String> newParts = new ArrayList<>();
                    for (int j = 0; j < i; j++) newParts.add(filterParts[j]);
                    newParts.addAll(link.getFilterSegments());
                    for (int j = i + 1; j < filterParts.length; j++) newParts.add(filterParts[j]);
                    remaining = String.join("/", newParts);
                    extraParams.putAll(link.getParams());
                    filterShortlink = "filter@" + code;
                    break; // one filter@ per path
                }
            }
        }

        // Extract date@VALUE from final segment (reserved segment).
        // "date" is a globally hard-reserved segment name. Does NOT count against @id limit.
        String dateParam = null;
        if (remaining.contains("@")) {
            String[] dateParts = remaining.split("/");
            String finalSeg = dateParts[dateParts.length - 1];
            if (finalSeg.startsWith("date@")) {
                String dateValue = finalSeg.substring(5); // strip "date@"
                if (dateValue.isEmpty()) {
                    throw new MonikerParseException("Empty date value in 'date@'.");
                }
                if (validate && !DATE_PARAM_PATTERN.matcher(dateValue).matches()) {
                    throw new MonikerParseException(
                        String.format("Invalid date parameter: '%s'. " +
                            "Must be YYYYMMDD, relative (e.g., 3M, 1Y, 5D), " +
                            "or symbolic (latest, previous).", dateValue)
                    );
                }
                dateParam = dateValue;
                // Remove the date segment from the path
                String[] newDateParts = new String[dateParts.length - 1];
                System.arraycopy(dateParts, 0, newDateParts, 0, dateParts.length - 1);
                remaining = String.join("/", newDateParts);
            }
        }

        // Extract in-path segment identity (@id embedded in a path segment).
        // @ is ONLY valid as an identity parameter within a non-final segment.
        // @ at end of path is a parse error (old @version syntax is removed).
        int[] segmentIdIndex = null;
        String segmentIdValue = null;

        if (remaining.contains("@")) {
            String[] parts = remaining.split("/");

            // Find segments with @
            List<int[]> midAt = new ArrayList<>();  // {index}
            List<String[]> midAtText = new ArrayList<>();  // {text}
            List<String> finalAtText = new ArrayList<>();

            for (int i = 0; i < parts.length; i++) {
                if (parts[i].contains("@")) {
                    if (i < parts.length - 1) {
                        midAt.add(new int[]{i});
                        midAtText.add(new String[]{parts[i]});
                    } else {
                        finalAtText.add(parts[i]);
                    }
                }
            }

            // @ in the final segment is a parse error
            if (!finalAtText.isEmpty()) {
                throw new MonikerParseException(
                    String.format("Invalid use of '@' at end of path in '%s'. " +
                                 "The @ character is only valid as an identity parameter " +
                                 "within a mid-path segment (e.g., segment@id/rest).", finalAtText.get(0))
                );
            }

            if (!midAt.isEmpty()) {
                if (midAt.size() > 1) {
                    throw new MonikerParseException(
                        "At most one @id identity parameter is allowed per path."
                    );
                }

                int segIdx = midAt.get(0)[0];
                String segText = midAtText.get(0)[0];
                int atPos = segText.indexOf('@');
                String segName = segText.substring(0, atPos);
                String idValue = segText.substring(atPos + 1);

                if (idValue.isEmpty()) {
                    throw new MonikerParseException(
                        String.format("Empty @id value in segment '%s'.", segText)
                    );
                }
                if (validate && !SEGMENT_ID_VALUE_PATTERN.matcher(idValue).matches()) {
                    throw new MonikerParseException(
                        String.format("Invalid segment identity value: '%s'. " +
                                     "Must contain only alphanumerics, hyphens, underscores, or dots.", idValue)
                    );
                }

                segmentIdIndex = new int[]{segIdx};
                segmentIdValue = idValue;
                // Replace the segment with the clean name
                parts[segIdx] = segName;
                remaining = String.join("/", parts);
            }
        }

        // Parse path
        MonikerPath path = parsePath(remaining, validate);

        // Parse query params (shortlink params first, client params override)
        QueryParams params = new QueryParams();
        for (java.util.Map.Entry<String, String> entry : extraParams.entrySet()) {
            params.put(entry.getKey(), entry.getValue());
        }
        if (queryStr != null && !queryStr.isEmpty()) {
            for (String pair : queryStr.split("&")) {
                int eqIdx = pair.indexOf('=');
                if (eqIdx != -1) {
                    try {
                        String key = URLDecoder.decode(pair.substring(0, eqIdx), "UTF-8");
                        String value = URLDecoder.decode(pair.substring(eqIdx + 1), "UTF-8");
                        params.put(key, value);
                    } catch (UnsupportedEncodingException e) {
                        // UTF-8 is always supported
                    }
                } else {
                    try {
                        params.put(URLDecoder.decode(pair, "UTF-8"), "");
                    } catch (UnsupportedEncodingException e) {
                        // UTF-8 is always supported
                    }
                }
            }
        }

        return new Moniker(path, namespace, segmentIdIndex, segmentIdValue, dateParam, filterShortlink, revision, params);
    }

    /**
     * Parse a moniker with validation enabled.
     */
    public static Moniker parseMoniker(String monikerStr) throws MonikerParseException {
        return parse(monikerStr, true, null);
    }

    /**
     * Parse a moniker with validation and an optional shortlink store.
     */
    public static Moniker parseMoniker(String monikerStr, ShortlinkStore store) throws MonikerParseException {
        return parse(monikerStr, true, store);
    }

    /**
     * Normalize a moniker string to canonical form.
     */
    public static String normalizeMoniker(String monikerStr) throws MonikerParseException {
        Moniker m = parseMoniker(monikerStr);
        return m.toString();
    }

    /**
     * Build a moniker from components.
     */
    public static Moniker buildMoniker(String pathStr, String namespace,
                                      Integer revision, QueryParams params) throws MonikerParseException {
        MonikerPath path = parsePath(pathStr, true);

        if (params == null) {
            params = new QueryParams();
        }

        return new Moniker(path, namespace, revision, params);
    }
}
