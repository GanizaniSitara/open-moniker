import { Container, Typography, Box } from "@mui/material";
import TechAppGrid from "@/components/TechAppGrid";
import { fetchApplications } from "@/lib/api-client";
import { getAllTechnicalProfiles } from "@/lib/tech-mock-data";

export default async function TechnicalCatalogPage() {
  const appsRes = await fetchApplications();
  const profiles = getAllTechnicalProfiles();

  const profileMap = new Map(profiles.map((p) => [p.appKey, p]));

  const applications = appsRes.applications
    .filter((a) => profileMap.has(a.key))
    .map((a) => ({
      appKey: a.key,
      displayName: a.display_name,
      color: a.color,
      profile: profileMap.get(a.key)!,
    }));

  return (
    <>
      <Box
        sx={{
          bgcolor: "#e9ecef",
          px: 3,
          py: 1,
        }}
      >
        <Typography
          variant="body2"
          sx={{ fontWeight: 700, textTransform: "uppercase" }}
        >
          Technical Catalog
        </Typography>
        <Typography variant="caption" color="text.secondary">
          CMDB infrastructure metadata — internal tech use only
        </Typography>
      </Box>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <TechAppGrid applications={applications} />
      </Container>
    </>
  );
}
