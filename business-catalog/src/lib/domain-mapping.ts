/**
 * Maps a catalog key to a domain key using prefix matching.
 *
 * For keys like "fixed_income.govies/treasury", extract "fixed_income" (before first . or /).
 * For keys like "benchmarks.constituents", extract "benchmarks".
 * For keys like "securities/lookup", extract "securities".
 */
export function catalogKeyToDomain(
  catalogKey: string,
  domainKeys: string[]
): string | null {
  // Try exact match first
  if (domainKeys.includes(catalogKey)) {
    return catalogKey;
  }

  // Extract the first segment: split on / first, then take prefix before first .
  const beforeSlash = catalogKey.split("/")[0];
  const beforeDot = beforeSlash.split(".")[0];

  // Try the full part before slash (e.g., "fixed_income.govies" -> try "fixed_income.govies")
  if (domainKeys.includes(beforeSlash)) {
    return beforeSlash;
  }

  // Try progressively shorter dot-prefixes
  const dotParts = beforeSlash.split(".");
  for (let i = dotParts.length; i >= 1; i--) {
    const prefix = dotParts.slice(0, i).join(".");
    // Convert dots to underscores for domain matching (e.g., "fixed.income" -> "fixed_income")
    const underscorePrefix = prefix.replace(/\./g, "_");
    if (domainKeys.includes(prefix)) {
      return prefix;
    }
    if (domainKeys.includes(underscorePrefix)) {
      return underscorePrefix;
    }
  }

  return null;
}

/**
 * Glob-style pattern matching (port of Python _pattern_matches).
 * Supports * (single segment) and ** (any number of segments).
 */
export function patternMatches(pattern: string, path: string): boolean {
  // Escape regex special chars except * and /
  let regexPattern = pattern.replace(/[.+?^${}()|[\]\\]/g, "\\$&");

  // Convert ** to match any segments (including /)
  regexPattern = regexPattern.replace(/\*\*/g, "%%DOUBLESTAR%%");

  // Convert single * to match single segment (no /)
  regexPattern = regexPattern.replace(/\*/g, "[^/]*");

  // Replace doublestar placeholder
  regexPattern = regexPattern.replace(/%%DOUBLESTAR%%/g, ".*");

  // Anchor
  regexPattern = `^${regexPattern}$`;

  try {
    return new RegExp(regexPattern).test(path);
  } catch {
    return false;
  }
}
