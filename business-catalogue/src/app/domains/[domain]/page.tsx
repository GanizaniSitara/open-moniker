import {
  Container,
  Typography,
  Box,
  Paper,
  Chip,
} from "@mui/material";
import Breadcrumbs from "@/components/Breadcrumbs";
import DatasetCard from "@/components/DatasetCard";
import { fetchDomain, fetchNodes, toSlashPath } from "@/lib/api-client";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ domain: string }>;
}

export default async function DomainDetailPage({ params }: PageProps) {
  const { domain: rawDomainKey } = await params;
  const domainKey = decodeURIComponent(rawDomainKey);

  let domainRes;
  try {
    domainRes = await fetchDomain(domainKey);
  } catch {
    notFound();
  }

  const domain = domainRes.domain;

  // Fetch all nodes, filter to this domain's datasets (prefix match + explicit domain mapping)
  const nodesRes = await fetchNodes();
  const datasets = nodesRes.nodes
    .filter((n) =>
      n.resolved_domain === domainKey ||
      n.domain === domainKey ||
      n.path === domainKey ||
      n.path.startsWith(domainKey + ".") ||
      n.path.startsWith(domainKey + "/")
    )
    .sort((a, b) => a.display_name.localeCompare(b.display_name));
  const leafDatasets = datasets.filter((d) => d.is_leaf);

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Domains", href: "/domains" },
          { label: domain.display_name },
        ]}
      />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
            <Typography variant="h4" sx={{ color: "#022D5E" }}>
              {domain.display_name}
            </Typography>
            <Box
              sx={{
                bgcolor: domain.color,
                color: "white",
                fontWeight: 600,
                fontSize: "0.75rem",
                px: 1,
                py: 0.3,
                borderRadius: "4px",
              }}
            >
              {domain.short_code}
            </Box>
          </Box>
          <Typography variant="body1" sx={{ mb: 2, color: "#53565A" }}>
            {domain.notes}
          </Typography>

          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
            <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary">
                Owner
              </Typography>
              <Typography variant="body2">{domain.owner}</Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary">
                Business Steward
              </Typography>
              <Typography variant="body2">{domain.business_steward}</Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary">
                Tech Custodian
              </Typography>
              <Typography variant="body2">{domain.tech_custodian}</Typography>
            </Paper>
          </Box>

          <Box sx={{ mt: 2, display: "flex", gap: 1, flexWrap: "wrap" }}>
            <Chip label={domain.data_category} size="small" variant="outlined" />
            <Chip
              label={domain.confidentiality}
              size="small"
              color={domain.confidentiality === "confidential" ? "warning" : "default"}
              variant="outlined"
            />
            <Chip label={domain.help_channel} size="small" variant="outlined" />
            {domain.wiki_link && (
              <a href={domain.wiki_link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
                <Chip
                  label="Wiki"
                  size="small"
                  clickable
                  variant="outlined"
                  sx={{ color: "#005587" }}
                />
              </a>
            )}
          </Box>
        </Box>

        {/* Datasets */}
        <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
          Datasets ({leafDatasets.length})
        </Typography>
        <Box>
          {datasets.map((ds) => (
            <DatasetCard
              key={ds.path}
              datasetKey={toSlashPath(ds.path)}
              displayName={ds.display_name}
              description={ds.description}
              sourceType={ds.source_binding?.type}
              domainDisplayName={domain.display_name}
              domainColor={domain.color}
              columnCount={0}
              classification={ds.classification}
              isContainer={!ds.is_leaf}
              columns={[]}
            />
          ))}
        </Box>
      </Container>
    </>
  );
}
