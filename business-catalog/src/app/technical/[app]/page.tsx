import { Container, Typography, Box, Chip } from "@mui/material";
import Breadcrumbs from "@/components/Breadcrumbs";
import { fetchApplication } from "@/lib/api-client";
import { getTechnicalProfile } from "@/lib/tech-mock-data";
import { notFound } from "next/navigation";

import CmdbSection from "@/components/technical/CmdbSection";
import InfraSection from "@/components/technical/InfraSection";
import SlaSection from "@/components/technical/SlaSection";
import DependencySection from "@/components/technical/DependencySection";
import DependencyDiagram from "@/components/technical/DependencyDiagram";
import ApiEndpointTable from "@/components/technical/ApiEndpointTable";
import DiagramSection from "@/components/technical/DiagramSection";
import TechDebtSection from "@/components/technical/TechDebtSection";

interface PageProps {
  params: Promise<{ app: string }>;
}

const healthColor: Record<string, "success" | "warning" | "error"> = {
  healthy: "success",
  degraded: "warning",
  critical: "error",
};

export default async function TechnicalDetailPage({ params }: PageProps) {
  const { app: rawAppKey } = await params;
  const appKey = decodeURIComponent(rawAppKey);

  let appRes;
  try {
    appRes = await fetchApplication(appKey);
  } catch {
    notFound();
  }

  const profile = getTechnicalProfile(appKey);
  if (!profile) {
    notFound();
  }

  const app = appRes.application;

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Technical Catalog", href: "/technical" },
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
              label={profile.sla.health_status}
              size="small"
              color={healthColor[profile.sla.health_status]}
            />
            <Chip
              label={profile.cmdb.ci_id}
              size="small"
              sx={{
                bgcolor: "#022D5E",
                color: "white",
                fontWeight: 600,
                fontFamily: "monospace",
              }}
            />
            <Chip
              label={profile.cmdb.business_criticality}
              size="small"
              variant="outlined"
            />
            <Chip
              label={profile.cmdb.operational_status}
              size="small"
              variant="outlined"
            />
          </Box>
          <Typography variant="body1" sx={{ color: "#53565A" }}>
            {app.description}
          </Typography>
        </Box>

        <CmdbSection cmdb={profile.cmdb} />
        <InfraSection infrastructure={profile.infrastructure} />
        <SlaSection sla={profile.sla} />
        <DependencyDiagram
          appKey={appKey}
          appName={app.display_name}
          upstream={profile.dependencies.upstream}
          downstream={profile.dependencies.downstream}
        />
        <DependencySection
          upstream={profile.dependencies.upstream}
          downstream={profile.dependencies.downstream}
        />
        <ApiEndpointTable endpoints={profile.api_endpoints} />
        <DiagramSection diagrams={profile.diagrams} />
        <TechDebtSection techDebt={profile.tech_debt} />
      </Container>
    </>
  );
}
