import { Container } from "@mui/material";
import ApplicationGrid from "@/components/ApplicationGrid";
import PageTitle from "@/components/PageTitle";
import { fetchApplications } from "@/lib/api-client";

export default async function ApplicationsPage() {
  const appsRes = await fetchApplications();

  const applications = appsRes.applications.map((a) => ({
    appKey: a.key,
    displayName: a.display_name,
    description: a.description,
    color: a.color,
    category: a.category,
    status: a.status,
    owner: a.owner,
    datasetCount: a.datasets.length,
    fieldCount: a.fields.length,
  }));

  return (
    <>
      <PageTitle title="Applications" />
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <ApplicationGrid applications={applications} />
      </Container>
    </>
  );
}
