import {
  Container,
  Typography,
  Box,
  Paper,
  Chip,
  Grid2 as Grid,
  Link as MuiLink,
} from "@mui/material";
import Breadcrumbs from "@/components/Breadcrumbs";
import SchemaTable from "@/components/SchemaTable";
import RelatedModels from "@/components/RelatedModels";
import SourceBadge from "@/components/SourceBadge";
import { getCatalogData } from "@/lib/data-loader";
import { sanitizeConfig } from "@/lib/sanitize";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ moniker: string[] }>;
}

export default async function DatasetDetailPage({ params }: PageProps) {
  const { moniker } = await params;
  const key = moniker.join("/");
  const data = getCatalogData();
  const dataset = data.datasetByKey.get(key);

  if (!dataset) notFound();

  const domain = dataset.domainKey
    ? data.domainByKey.get(dataset.domainKey)
    : null;
  const relatedModels = data.modelsForDataset.get(key) || [];
  const sanitizedConfig = dataset.source_binding?.config
    ? sanitizeConfig(dataset.source_binding.config)
    : null;

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Datasets", href: "/datasets" },
          ...(domain
            ? [
                {
                  label: domain.display_name,
                  href: `/domains/${domain.key}`,
                },
              ]
            : []),
          { label: dataset.display_name },
        ]}
      />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}
          >
            <Typography variant="h4" sx={{ color: "#022D5E" }}>
              {dataset.display_name}
            </Typography>
            {dataset.source_binding && (
              <SourceBadge type={dataset.source_binding.type} />
            )}
            {dataset.isContainer && (
              <Chip label="Container" size="small" variant="outlined" />
            )}
          </Box>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontFamily: "monospace" }}
          >
            {dataset.key}
          </Typography>
          {dataset.description && (
            <Typography variant="body1" sx={{ mt: 1, color: "#53565A" }}>
              {dataset.description}
            </Typography>
          )}
        </Box>

        <Grid container spacing={3}>
          {/* Left column: main content */}
          <Grid size={{ xs: 12, md: 8 }}>
            {/* Schema */}
            {dataset.schema?.columns && dataset.schema.columns.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Schema ({dataset.schema.columns.length} columns)
                </Typography>
                <SchemaTable columns={dataset.schema.columns} />
                {dataset.schema.semantic_tags &&
                  dataset.schema.semantic_tags.length > 0 && (
                    <Box
                      sx={{
                        mt: 1.5,
                        display: "flex",
                        gap: 0.5,
                        flexWrap: "wrap",
                      }}
                    >
                      {dataset.schema.semantic_tags.map((tag) => (
                        <Chip
                          key={tag}
                          label={tag}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  )}
                {dataset.schema.use_cases &&
                  dataset.schema.use_cases.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Use Cases
                      </Typography>
                      <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                        {dataset.schema.use_cases.map((uc, i) => (
                          <li key={i}>
                            <Typography variant="body2">{uc}</Typography>
                          </li>
                        ))}
                      </ul>
                    </Box>
                  )}
              </Box>
            )}

            {/* Source binding */}
            {dataset.source_binding && sanitizedConfig && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Source Configuration
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    sx={{ mb: 1 }}
                  >
                    Type: {dataset.source_binding.type.toUpperCase()}
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      fontSize: "0.8rem",
                      fontFamily: "monospace",
                      bgcolor: "#f8f9fa",
                      p: 2,
                      borderRadius: 1,
                      overflow: "auto",
                      maxHeight: 300,
                      m: 0,
                    }}
                  >
                    {JSON.stringify(sanitizedConfig, null, 2)}
                  </Box>
                </Paper>
              </Box>
            )}

            {/* Related models */}
            {relatedModels.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Related Business Models ({relatedModels.length})
                </Typography>
                <RelatedModels models={relatedModels} />
              </Box>
            )}

            {/* Access policy */}
            {dataset.access_policy && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Access Policy
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  {dataset.access_policy.min_filters != null && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      Minimum filters required:{" "}
                      {dataset.access_policy.min_filters}
                    </Typography>
                  )}
                  {dataset.access_policy.max_rows_warn != null && (
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      Row warning threshold:{" "}
                      {dataset.access_policy.max_rows_warn.toLocaleString()}
                    </Typography>
                  )}
                  {dataset.access_policy.denial_message && (
                    <Box
                      component="pre"
                      sx={{
                        fontSize: "0.8rem",
                        fontFamily: "monospace",
                        bgcolor: "#fff8e1",
                        p: 1.5,
                        borderRadius: 1,
                        whiteSpace: "pre-wrap",
                        mt: 1,
                      }}
                    >
                      {dataset.access_policy.denial_message}
                    </Box>
                  )}
                </Paper>
              </Box>
            )}
          </Grid>

          {/* Right column: metadata sidebar */}
          <Grid size={{ xs: 12, md: 4 }}>
            {/* Ownership */}
            {dataset.ownership && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Ownership
                </Typography>
                {dataset.ownership.accountable_owner && (
                  <MetaRow
                    label="Owner"
                    value={dataset.ownership.accountable_owner}
                  />
                )}
                {dataset.ownership.data_specialist && (
                  <MetaRow
                    label="Data Specialist"
                    value={dataset.ownership.data_specialist}
                  />
                )}
                {dataset.ownership.support_channel && (
                  <MetaRow
                    label="Support"
                    value={dataset.ownership.support_channel}
                  />
                )}
                {dataset.ownership.adop && (
                  <MetaRow label="ADOP" value={dataset.ownership.adop} />
                )}
                {dataset.ownership.ads && (
                  <MetaRow label="ADS" value={dataset.ownership.ads} />
                )}
                {dataset.ownership.adal && (
                  <MetaRow label="ADAL" value={dataset.ownership.adal} />
                )}
              </Paper>
            )}

            {/* Classification */}
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography
                variant="subtitle1"
                sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
              >
                Classification
              </Typography>
              <Chip
                label={dataset.classification || "internal"}
                size="small"
                variant="outlined"
                color={
                  dataset.classification === "confidential"
                    ? "warning"
                    : dataset.classification === "restricted"
                    ? "error"
                    : "default"
                }
              />
            </Paper>

            {/* Documentation */}
            {dataset.documentation && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Documentation
                </Typography>
                {Object.entries(dataset.documentation)
                  .filter(([k, v]) => typeof v === "string")
                  .map(([k, v]) => (
                    <Box key={k} sx={{ mb: 0.5 }}>
                      <MuiLink
                        href={v as string}
                        target="_blank"
                        variant="body2"
                        sx={{ textTransform: "capitalize", color: "#005587" }}
                      >
                        {k.replace(/_/g, " ")}
                      </MuiLink>
                    </Box>
                  ))}
              </Paper>
            )}

            {/* Domain */}
            {domain && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Domain
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Box
                    sx={{
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      bgcolor: domain.color,
                    }}
                  />
                  <Typography variant="body2">{domain.display_name}</Typography>
                </Box>
              </Paper>
            )}
          </Grid>
        </Grid>
      </Container>
    </>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <Box sx={{ mb: 1 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}
