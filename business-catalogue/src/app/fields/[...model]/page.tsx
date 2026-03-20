import {
  Container,
  Typography,
  Box,
  Paper,
  Chip,
  Link as MuiLink,
} from "@mui/material";
import Breadcrumbs from "@/components/Breadcrumbs";
import AppearsInTable from "@/components/AppearsInTable";
import TrustIndicator from "@/components/contributions/TrustIndicator";
import SidebarToggle from "@/components/contributions/SidebarToggle";
import SuggestEditButton from "@/components/contributions/SuggestEditButton";
import HelpfulVote from "@/components/contributions/HelpfulVote";
import { fetchModel, fetchNodes, toSlashPath } from "@/lib/api-client";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ model: string[] }>;
}

export default async function FieldDetailPage({ params }: PageProps) {
  const { model: modelSegments } = await params;
  const path = modelSegments.join("/");

  let modelRes;
  try {
    modelRes = await fetchModel(path);
  } catch {
    notFound();
  }

  const model = modelRes.model;

  // Find parent container for breadcrumbs
  const parentPath = path.split("/").slice(0, -1).join("/");
  let parentName: string | null = null;
  if (parentPath) {
    try {
      const parentRes = await fetchModel(parentPath);
      parentName = parentRes.model.display_name;
    } catch {
      // Parent may not exist as a model
    }
  }

  // Resolve appears_in patterns to actual datasets
  const isContainer = model.appears_in.length === 0;
  let appearsInEntries: {
    datasetKey: string;
    displayName: string;
    sourceType?: string;
    columnName?: string;
    notes?: string;
  }[] = [];

  if (model.appears_in.length > 0) {
    try {
      const nodesRes = await fetchNodes();
      const nodeByPath = new Map(nodesRes.nodes.map((n) => [n.path, n]));

      for (const link of model.appears_in) {
        // Match pattern against node paths
        const pattern = link.moniker_pattern;
        for (const node of nodesRes.nodes) {
          if (!node.is_leaf) continue;
          if (patternMatches(pattern, node.path)) {
            appearsInEntries.push({
              datasetKey: toSlashPath(node.path),
              displayName: node.display_name,
              sourceType: node.source_binding?.type,
              columnName: link.column_name || undefined,
              notes: link.notes || undefined,
            });
          }
        }
      }

      // Deduplicate by dataset key
      const seen = new Set<string>();
      appearsInEntries = appearsInEntries.filter((e) => {
        if (seen.has(e.datasetKey)) return false;
        seen.add(e.datasetKey);
        return true;
      });
    } catch {
      // Node lookup is optional
    }
  }

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Fields", href: "/fields" },
          ...(parentName
            ? [{ label: parentName, href: `/fields/${parentPath}` }]
            : []),
          { label: model.display_name },
        ]}
      />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
            <TrustIndicator entityType="field" entityKey={path} />
            <Typography variant="h4" sx={{ color: "#022D5E" }}>
              {model.display_name}
            </Typography>
            <SidebarToggle entityType="field" entityKey={path} />
          </Box>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontFamily: "monospace", mb: 1 }}
          >
            {model.path}
          </Typography>
          {model.description && (
            <Typography variant="body1" sx={{ mb: 1, color: "#53565A" }}>
              {model.description}
            </Typography>
          )}
          <SuggestEditButton
            entityType="field"
            entityKey={path}
            fields={[
              { name: "description", label: "Description", currentValue: model.description },
              { name: "formula", label: "Formula", currentValue: model.formula },
              { name: "unit", label: "Unit", currentValue: model.unit },
              { name: "data_type", label: "Data Type", currentValue: model.data_type },
            ]}
          />

          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 2 }}>
            {model.formula && (
              <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
                <Typography variant="caption" color="text.secondary">
                  Formula
                </Typography>
                <Typography
                  variant="body1"
                  sx={{ fontFamily: "monospace", mt: 0.5 }}
                >
                  {model.formula}
                </Typography>
              </Paper>
            )}
            {model.unit && (
              <Paper variant="outlined" sx={{ p: 2, minWidth: 120 }}>
                <Typography variant="caption" color="text.secondary">
                  Unit
                </Typography>
                <Typography variant="body1" sx={{ mt: 0.5 }}>
                  {model.unit}
                </Typography>
              </Paper>
            )}
            {model.data_type && (
              <Paper variant="outlined" sx={{ p: 2, minWidth: 120 }}>
                <Typography variant="caption" color="text.secondary">
                  Data Type
                </Typography>
                <Typography variant="body1" sx={{ mt: 0.5 }}>
                  {model.data_type}
                </Typography>
              </Paper>
            )}
          </Box>

          {model.semantic_tags && model.semantic_tags.length > 0 && (
            <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 2 }}>
              {model.semantic_tags.map((tag) => (
                <Chip key={tag} label={tag} size="small" variant="outlined" />
              ))}
            </Box>
          )}
        </Box>

        {/* Aliases */}
        {model.aliases && model.aliases.length > 0 && (
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            <Typography
              variant="subtitle1"
              sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
            >
              Also Known As
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {model.aliases.map((alias, i) => (
                <Box
                  key={i}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    flexWrap: "wrap",
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: 600, fontFamily: "monospace" }}
                  >
                    {alias.name}
                  </Typography>
                  <Chip
                    label={alias.type.replace(/_/g, " ")}
                    size="small"
                    sx={{
                      fontSize: "0.65rem",
                      height: 20,
                      bgcolor:
                        alias.type === "abbreviation"
                          ? "#E3F2FD"
                          : alias.type === "legacy_name"
                            ? "#FFF3E0"
                            : alias.type === "system_name"
                              ? "#F3E5F5"
                              : alias.type === "vendor_name"
                                ? "#E8F5E9"
                                : "#F5F5F5",
                      color:
                        alias.type === "abbreviation"
                          ? "#1565C0"
                          : alias.type === "legacy_name"
                            ? "#E65100"
                            : alias.type === "system_name"
                              ? "#7B1FA2"
                              : alias.type === "vendor_name"
                                ? "#2E7D32"
                                : "#616161",
                    }}
                  />
                  {alias.context && (
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ flex: 1 }}
                    >
                      {alias.context}
                    </Typography>
                  )}
                </Box>
              ))}
            </Box>
          </Paper>
        )}

        {/* Ownership */}
        {model.ownership && (
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            <Typography
              variant="subtitle1"
              sx={{ mb: 1, fontWeight: 600, fontSize: "0.9rem" }}
            >
              Ownership
            </Typography>
            <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {model.ownership.methodology_owner && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Methodology Owner
                  </Typography>
                  <Typography variant="body2">
                    {model.ownership.methodology_owner}
                  </Typography>
                </Box>
              )}
              {model.ownership.business_steward && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Business Steward
                  </Typography>
                  <Typography variant="body2">
                    {model.ownership.business_steward}
                  </Typography>
                </Box>
              )}
              {model.ownership.support_channel && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Support
                  </Typography>
                  <Typography variant="body2">
                    {model.ownership.support_channel}
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
        )}

        {/* Documentation links */}
        {(model.documentation_url || model.methodology_url || model.wiki_link) && (
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            <Typography
              variant="subtitle1"
              sx={{ mb: 1, fontWeight: 600, fontSize: "0.9rem" }}
            >
              Documentation
            </Typography>
            {model.documentation_url && (
              <Box sx={{ mb: 0.5 }}>
                <MuiLink
                  href={model.documentation_url}
                  target="_blank"
                  variant="body2"
                  sx={{ color: "#005587" }}
                >
                  Documentation
                </MuiLink>
              </Box>
            )}
            {model.methodology_url && (
              <Box sx={{ mb: 0.5 }}>
                <MuiLink
                  href={model.methodology_url}
                  target="_blank"
                  variant="body2"
                  sx={{ color: "#005587" }}
                >
                  Methodology
                </MuiLink>
              </Box>
            )}
            {model.wiki_link && (
              <Box>
                <MuiLink
                  href={model.wiki_link}
                  target="_blank"
                  variant="body2"
                  sx={{ color: "#005587" }}
                >
                  Wiki
                </MuiLink>
              </Box>
            )}
          </Paper>
        )}

        {/* Appears in */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
            Appears In ({appearsInEntries.length} datasets)
          </Typography>
          {appearsInEntries.length > 0 ? (
            <AppearsInTable entries={appearsInEntries} />
          ) : (
            <Typography variant="body2" color="text.secondary">
              {isContainer
                ? "This is a container grouping. Browse the individual fields below."
                : "No matching datasets found for the appears_in patterns."}
            </Typography>
          )}
        </Box>

        {/* Raw appears_in patterns */}
        {model.appears_in && model.appears_in.length > 0 && (
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography
              variant="subtitle1"
              sx={{ mb: 1, fontWeight: 600, fontSize: "0.9rem" }}
            >
              Matching Patterns
            </Typography>
            {model.appears_in.map((link, i) => (
              <Box key={i} sx={{ mb: 1 }}>
                <Typography
                  variant="body2"
                  sx={{ fontFamily: "monospace", fontSize: "0.85rem" }}
                >
                  {link.moniker_pattern}
                  {link.column_name && ` → ${link.column_name}`}
                </Typography>
                {link.notes && (
                  <Typography variant="caption" color="text.secondary">
                    {link.notes}
                  </Typography>
                )}
              </Box>
            ))}
          </Paper>
        )}

        <HelpfulVote entityType="field" entityKey={path} />
      </Container>
    </>
  );
}

/** Simple glob-style pattern matcher (supports * wildcard) */
function patternMatches(pattern: string, path: string): boolean {
  if (pattern === path) return true;
  if (!pattern.includes("*")) return false;
  const regex = new RegExp(
    "^" + pattern.replace(/\*/g, "[^/]*") + "$"
  );
  return regex.test(path);
}
