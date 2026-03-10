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
import { getCatalogData } from "@/lib/data-loader";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ model: string[] }>;
}

export default async function FieldDetailPage({ params }: PageProps) {
  const { model: modelSegments } = await params;
  const key = modelSegments.join("/");
  const data = await getCatalogData();
  const model = data.modelByKey.get(key);

  if (!model) notFound();

  const appearsIn = data.datasetsForModel.get(key) || [];

  const parentKey = key.split("/").slice(0, -1).join("/");
  const parent = parentKey ? data.modelByKey.get(parentKey) : null;

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Fields", href: "/fields" },
          ...(parent
            ? [{ label: parent.display_name, href: `/fields/${parent.key}` }]
            : []),
          { label: model.display_name },
        ]}
      />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ mb: 1, color: "#022D5E" }}>
            {model.display_name}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontFamily: "monospace", mb: 1 }}
          >
            {model.key}
          </Typography>
          {model.description && (
            <Typography variant="body1" sx={{ mb: 2, color: "#53565A" }}>
              {model.description}
            </Typography>
          )}

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
        {(model.documentation_url || model.methodology_url) && (
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
              <Box>
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
          </Paper>
        )}

        {/* Appears in */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
            Appears In ({appearsIn.length} datasets)
          </Typography>
          {appearsIn.length > 0 ? (
            <AppearsInTable entries={appearsIn} />
          ) : (
            <Typography variant="body2" color="text.secondary">
              {model.isContainer
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
      </Container>
    </>
  );
}
