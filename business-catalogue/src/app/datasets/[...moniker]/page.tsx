import {
  Container,
  Typography,
  Box,
  Paper,
  Chip,
  Grid2 as Grid,
  Link as MuiLink,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
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

            {/* Technical details — collapsed by default */}
            {(dataset.source_binding || dataset.access_policy) && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Technical Details
                </Typography>

                {dataset.source_binding && sanitizedConfig && (
                  <Accordion
                    disableGutters
                    variant="outlined"
                    sx={{ "&:before": { display: "none" } }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle2">
                        Source Configuration — {dataset.source_binding.type.toUpperCase()}
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
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
                    </AccordionDetails>
                  </Accordion>
                )}

                {dataset.access_policy && (
                  <Accordion
                    disableGutters
                    variant="outlined"
                    sx={{ "&:before": { display: "none" } }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle2">
                        Access Policy
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
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
                    </AccordionDetails>
                  </Accordion>
                )}
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
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
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
                  <MuiLink
                    href={`/domains/${domain.key}`}
                    variant="body2"
                    sx={{ color: "#005587" }}
                  >
                    {domain.display_name}
                  </MuiLink>
                </Box>
              </Paper>
            )}

            {/* Tags */}
            {((dataset.semantic_tags && dataset.semantic_tags.length > 0) ||
              (dataset.schema?.semantic_tags &&
                dataset.schema.semantic_tags.length > 0)) && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Tags
                </Typography>
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                  {[
                    ...(dataset.semantic_tags || []),
                    ...(dataset.schema?.semantic_tags || []),
                  ]
                    .filter((v, i, a) => a.indexOf(v) === i)
                    .map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                </Box>
              </Paper>
            )}

            {/* Use Cases */}
            {dataset.schema?.use_cases &&
              dataset.schema.use_cases.length > 0 && (
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography
                    variant="subtitle1"
                    sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                  >
                    Use Cases
                  </Typography>
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {dataset.schema.use_cases.map((uc, i) => (
                      <li key={i}>
                        <Typography variant="body2">{uc}</Typography>
                      </li>
                    ))}
                  </ul>
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
