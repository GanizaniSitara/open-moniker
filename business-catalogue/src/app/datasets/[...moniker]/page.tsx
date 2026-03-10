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
import { fetchDescribe } from "@/lib/api-client";
import { notFound } from "next/navigation";
import type { Model } from "@/lib/types";

interface PageProps {
  params: Promise<{ moniker: string[] }>;
}

export default async function DatasetDetailPage({ params }: PageProps) {
  const { moniker } = await params;
  const key = moniker.join("/");

  // Fetch describe (rich metadata) and catalog data (domain + cross-refs) in parallel
  const [describeData, catalogData] = await Promise.all([
    fetchDescribe(key).catch(() => null),
    getCatalogData(),
  ]);

  if (!describeData) notFound();

  // Domain from catalog data
  const dataset = catalogData.datasetByKey.get(key);
  const domain = dataset?.domainKey
    ? catalogData.domainByKey.get(dataset.domainKey)
    : null;

  // Related models: prefer describe response, fall back to cross-ref
  const describeModels: Model[] = (describeData.models || []).map((m) => ({
    key: m.path,
    display_name: m.display_name,
    description: m.description,
    formula: m.formula || undefined,
    unit: m.unit || undefined,
    isContainer: false,
  }));
  const relatedModels =
    describeModels.length > 0
      ? describeModels
      : catalogData.modelsForDataset.get(key) || [];

  // Ownership from describe
  const ownership = describeData.ownership as {
    accountable_owner?: string;
    data_specialist?: string;
    support_channel?: string;
    adop?: string;
    ads?: string;
    adal?: string;
  };
  const hasOwnership = ownership && Object.values(ownership).some((v) => v);

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Datasets", href: "/datasets" },
          ...(domain
            ? [
                {
                  label: domain.display_name,
                  href: `/categories/${domain.key}`,
                },
              ]
            : []),
          { label: describeData.display_name || key },
        ]}
      />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}
          >
            <Typography variant="h4" sx={{ color: "#022D5E" }}>
              {describeData.display_name || key}
            </Typography>
            {describeData.source_type && (
              <SourceBadge type={describeData.source_type} />
            )}
            {!describeData.has_source_binding && (
              <Chip label="Container" size="small" variant="outlined" />
            )}
          </Box>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontFamily: "monospace" }}
          >
            {describeData.path}
          </Typography>
          {describeData.description && (
            <Typography variant="body1" sx={{ mt: 1, color: "#53565A" }}>
              {describeData.description}
            </Typography>
          )}
        </Box>

        <Grid container spacing={3}>
          {/* Left column: main content */}
          <Grid size={{ xs: 12, md: 8 }}>
            {/* Schema */}
            {describeData.schema?.columns &&
              describeData.schema.columns.length > 0 && (
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h5" sx={{ mb: 2, color: "#022D5E" }}>
                    Schema ({describeData.schema.columns.length} columns)
                  </Typography>
                  <SchemaTable columns={describeData.schema.columns} />
                  {describeData.schema.semantic_tags &&
                    describeData.schema.semantic_tags.length > 0 && (
                      <Box
                        sx={{
                          mt: 1.5,
                          display: "flex",
                          gap: 0.5,
                          flexWrap: "wrap",
                        }}
                      >
                        {describeData.schema.semantic_tags.map((tag) => (
                          <Chip
                            key={tag}
                            label={tag}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    )}
                  {describeData.schema.use_cases &&
                    describeData.schema.use_cases.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Use Cases
                        </Typography>
                        <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                          {describeData.schema.use_cases.map((uc, i) => (
                            <li key={i}>
                              <Typography variant="body2">{uc}</Typography>
                            </li>
                          ))}
                        </ul>
                      </Box>
                    )}
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
          </Grid>

          {/* Right column: metadata sidebar */}
          <Grid size={{ xs: 12, md: 4 }}>
            {/* Ownership */}
            {hasOwnership && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Ownership
                </Typography>
                {ownership.accountable_owner && (
                  <MetaRow
                    label="Owner"
                    value={ownership.accountable_owner}
                  />
                )}
                {ownership.data_specialist && (
                  <MetaRow
                    label="Data Specialist"
                    value={ownership.data_specialist}
                  />
                )}
                {ownership.support_channel && (
                  <MetaRow
                    label="Support"
                    value={ownership.support_channel}
                  />
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
                label={describeData.classification || "internal"}
                size="small"
                variant="outlined"
                color={
                  describeData.classification === "confidential"
                    ? "warning"
                    : describeData.classification === "restricted"
                    ? "error"
                    : "default"
                }
              />
            </Paper>

            {/* Documentation */}
            {describeData.documentation && (
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.9rem" }}
                >
                  Documentation
                </Typography>
                {Object.entries(describeData.documentation)
                  .filter(([, v]) => typeof v === "string" && v)
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
                  Category
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
