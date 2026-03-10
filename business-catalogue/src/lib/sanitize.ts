const SENSITIVE_KEYS = [
  "dsn",
  "password",
  "secret",
  "token",
  "api_key",
  "credentials",
  "connection_string",
  "base_url",
  "hosts",
];

/**
 * Sanitize source binding config by redacting sensitive fields.
 * Keeps type, database, schema, warehouse, format, sheet, and method.
 */
export function sanitizeConfig(
  config: Record<string, unknown>
): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(config)) {
    if (key === "query") {
      // Show query template but truncate if very long
      const q = String(value);
      sanitized[key] = q.length > 200 ? q.substring(0, 200) + "..." : q;
    } else if (SENSITIVE_KEYS.includes(key.toLowerCase())) {
      sanitized[key] = "••••••••";
    } else if (
      typeof value === "object" &&
      value !== null &&
      !Array.isArray(value)
    ) {
      sanitized[key] = sanitizeConfig(value as Record<string, unknown>);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}
