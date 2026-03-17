import {
  Container,
  Typography,
  Box,
  Paper,
  Chip,
  Link as MuiLink,
} from "@mui/material";
import Breadcrumbs from "@/components/Breadcrumbs";
import { fetchApplication } from "@/lib/api-client";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ app: string }>;
}

export default async function ApplicationDetailPage({ params }: PageProps) {
  const { app: rawAppKey } = await params;
  const appKey = decodeURIComponent(rawAppKey);

  let appRes;
  try {
    appRes = await fetchApplication(appKey);
  } catch {
    notFound();
  }

  const app = appRes.application;

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Applications", href: "/applications" },
          { label: app.display_name },
        ]}
      />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
            <Typography variant="h4" sx={{ color: "#022D5E" }}>
              {app.display_name}
            </Typography>
            <Chip
              label={app.status}
              size="small"
              color={
                app.status === "active"
                  ? "success"
                  : app.status === "decommissioned"
                  ? "error"
                  : "default"
              }
            />
            <Box
              sx={{
                bgcolor: app.color,
                color: "white",
                fontWeight: 600,
                fontSize: "0.75rem",
                px: 1,
                py: 0.3,
                borderRadius: "4px",
              }}
            >
              {app.category}
            </Box>
          </Box>
          <Typography variant="body1" sx={{ mb: 2, color: "#53565A" }}>
            {app.description}
          </Typography>

          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
            <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary">
                Owner
              </Typography>
              <Typography variant="body2">{app.owner || "—"}</Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary">
                Tech Lead
              </Typography>
              <Typography variant="body2">{app.tech_lead || "—"}</Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary">
                Support Channel
              </Typography>
              <Typography variant="body2">{app.support_channel || "—"}</Typography>
            </Paper>
          </Box>

          <Box sx={{ mt: 2, display: "flex", gap: 1, flexWrap: "wrap" }}>
            <Chip label={app.category} size="small" variant="outlined" />
            {app.support_channel && (
              <Chip label={app.support_channel} size="small" variant="outlined" />
            )}
            {app.documentation_url && (
              <a href={app.documentation_url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
                <Chip
                  label="Documentation"
                  size="small"
                  clickable
                  variant="outlined"
                  sx={{ color: "#005587" }}
                />
              </a>
            )}
            {app.wiki_link && (
              <a href={app.wiki_link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
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
          Datasets ({app.datasets.length} patterns)
        </Typography>
        {app.datasets.length > 0 ? (
          <Paper variant="outlined" sx={{ p: 2, mb: 4 }}>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              {app.datasets.map((pattern) => (
                <Chip
                  key={pattern}
                  label={pattern}
                  size="small"
                  sx={{
                    fontFamily: "monospace",
                    fontSize: "0.8rem",
                    bgcolor: "#f8f9fa",
                  }}
                />
              ))}
            </Box>
          </Paper>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
            No dataset patterns configured.
          </Typography>
        )}

        {/* Fields */}
        <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
          Fields ({app.fields.length})
        </Typography>
        {app.fields.length > 0 ? (
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              {app.fields.map((field) => (
                <MuiLink
                  key={field}
                  href={`/fields/${field.replace(/\//g, "/")}`}
                  sx={{ textDecoration: "none" }}
                >
                  <Chip
                    label={field}
                    size="small"
                    clickable
                    sx={{
                      fontFamily: "monospace",
                      fontSize: "0.8rem",
                      bgcolor: "#f0f7e6",
                      color: "#789D4A",
                      fontWeight: 600,
                    }}
                  />
                </MuiLink>
              ))}
            </Box>
          </Paper>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No field references configured.
          </Typography>
        )}
      </Container>
    </>
  );
}
