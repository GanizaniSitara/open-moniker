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
import { fetchDescribe, fetchDomains, fetchNode, toDotPath } from "@/lib/api-client";
import { sanitizeConfig } from "@/lib/sanitize";
import { getVendors } from "@/lib/vendors";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ moniker: string[] }>;
}

export default async function DatasetDetailPage({ params }: PageProps) {
  const { moniker } = await params;
  const urlPath = moniker.join("/");
  const monikerPath = toDotPath(urlPath);

  let desc;
  let nodeRes;
  try {
    [desc, nodeRes] = await Promise.all([
      fetchDescribe(urlPath),
      fetchNode(monikerPath),
    ]);
  } catch {
    notFound();
  }

  // Look up domain info (prefer resolved_domain which includes inheritance)
  let domain = null;
  const domainKey = nodeRes.node.resolved_domain || nodeRes.node.domain;
  if (domainKey) {
    try {
      const domainsRes = await fetchDomains();
      domain = domainsRes.domains.find((d) => d.name === domainKey) || null;
    } catch {
      // Domain lookup is optional
    }
  }

  const isContainer = !desc.has_source_binding;
  const sourceType = desc.source_type;
  const vendor = desc.vendor ? getVendors().find((v) => v.key === desc.vendor) : null;
  const sanitizedConfig = nodeRes.node.source_binding?.config
    ? sanitizeConfig(nodeRes.node.source_binding.config)
    : null;
  const columns = desc.schema?.columns || [];
  const models = desc.models || [];
  const ownership = desc.ownership;
  const tags = [
    ...(desc.tags || []),
    ...(desc.schema?.semantic_tags || []),
  ].filter((v, i, a) => a.indexOf(v) === i);
  const useCases = desc.schema?.use_cases || [];

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Datasets", href: "/datasets" },
          ...(domain
            ? [
                {
                  label: domain.display_name,
                  href: `/domains/${domain.name}`,
                },
              ]
            : []),
          { label: desc.display_name || monikerPath },
        ]}
      />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}
          >
            <Typography variant="h4" sx={{ color: "#022D5E" }}>
              {desc.display_name || monikerPath}
            </Typography>
            {sourceType && <SourceBadge type={sourceType} />}
            {isContainer && (
              <Chip label="Container" size="small" variant="outlined" />
            )}
          </Box>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontFamily: "monospace" }}
          >
            {monikerPath}
          </Typography>
          {desc.description && (
            <Typography variant="body1" sx={{ mt: 1, color: "#53565A" }}>
              {desc.description}
            </Typography>
          )}
          {desc.technical_description && (
            <Typography
              variant="body2"
              sx={{
                mt: 1,
                color: "#6B7280",
                bgcolor: "#f8f9fa",
                p: 1.5,
                borderRadius: "6px",
                borderLeft: "3px solid #d1d5db",
                fontStyle: "italic",
              }}
            >
              <strong style={{ fontStyle: "normal" }}>Technical:</strong>{" "}
              {desc.technical_description}
            </Typography>
          )}
        </Box>

        <Grid container spacing={3}>
          {/* Left column: main content */}
          <Grid size={{ xs: 12, md: 8 }}>
            {/* Schema */}
            {columns.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Schema ({columns.length} columns)
                </Typography>
                <SchemaTable
                  columns={columns.map((c) => ({
                    name: c.name,
                    type: c.type,
                    description: c.description,
                    semantic_type: c.semantic_type || undefined,
                    primary_key: c.primary_key,
                    foreign_key: c.foreign_key || undefined,
                  }))}
                />
              </Box>
            )}

            {/* Related models */}
            {models.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Related Business Models ({models.length})
                </Typography>
                <RelatedModels models={models} />
              </Box>
            )}

            {/* Technical details — collapsed by default */}
            {(sourceType || desc.access_policy) && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                  Technical Details
                </Typography>

                {sourceType && sanitizedConfig && (
                  <Accordion
                    disableGutters
                    variant="outlined"
                    sx={{ "&:before": { display: "none" } }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle2">
                        Source Configuration — {sourceType.toUpperCase()}
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

                {desc.access_policy && (
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
                      {desc.access_policy.min_filters != null && (
                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                          Minimum filters required:{" "}
                          {desc.access_policy.min_filters}
                        </Typography>
                      )}
                      {desc.access_policy.max_rows_warn != null && (
                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                          Row warning threshold:{" "}
                          {desc.access_policy.max_rows_warn.toLocaleString()}
                        </Typography>
                      )}
                      {desc.access_policy.denial_message && (
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
                          {desc.access_policy.denial_message}
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
            {ownership && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Ownership
                </Typography>
                {ownership.accountable_owner && (
                  <MetaRow label="Owner" value={ownership.accountable_owner} />
                )}
                {ownership.data_specialist && (
                  <MetaRow
                    label="Data Specialist"
                    value={ownership.data_specialist}
                  />
                )}
                {ownership.support_channel && (
                  <MetaRow label="Support" value={ownership.support_channel} />
                )}
                {ownership.adop && (
                  <MetaRow label="ADOP" value={ownership.adop} />
                )}
                {ownership.ads && (
                  <MetaRow label="ADS" value={ownership.ads} />
                )}
                {ownership.adal && (
                  <MetaRow label="ADAL" value={ownership.adal} />
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
                label={desc.classification || "internal"}
                size="small"
                variant="outlined"
                color={
                  desc.classification === "confidential"
                    ? "warning"
                    : desc.classification === "restricted"
                    ? "error"
                    : "default"
                }
              />
            </Paper>

            {/* Maturity */}
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography
                variant="subtitle1"
                sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
              >
                Maturity
              </Typography>
              <Chip
                label={(desc.maturity || "catalogued").charAt(0).toUpperCase() + (desc.maturity || "catalogued").slice(1)}
                size="small"
                color={
                  desc.maturity === "certified"
                    ? "success"
                    : desc.maturity === "governed"
                    ? "primary"
                    : "default"
                }
              />
            </Paper>

            {/* Documentation */}
            {desc.documentation && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Documentation
                </Typography>
                {Object.entries(desc.documentation)
                  .filter(
                    ([k, v]) => typeof v === "string" && k !== "additional"
                  )
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
                    href={`/domains/${domain.name}`}
                    variant="body2"
                    sx={{ color: "#005587" }}
                  >
                    {domain.display_name}
                  </MuiLink>
                </Box>
              </Paper>
            )}

            {/* Vendor */}
            {(vendor || desc.vendor) && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Vendor
                </Typography>
                <MuiLink
                  href={`/datasets?vendor=${desc.vendor}`}
                  variant="body2"
                  sx={{ color: "#005587" }}
                >
                  {vendor?.name || desc.vendor}
                </MuiLink>
                {vendor?.category && (
                  <Chip
                    label={vendor.category}
                    size="small"
                    variant="outlined"
                    sx={{ ml: 1, fontSize: "0.7rem" }}
                  />
                )}
              </Paper>
            )}

            {/* Tags */}
            {tags.length > 0 && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Tags
                </Typography>
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                  {tags.map((tag) => (
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
            {useCases.length > 0 && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Use Cases
                </Typography>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {useCases.map((uc, i) => (
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
