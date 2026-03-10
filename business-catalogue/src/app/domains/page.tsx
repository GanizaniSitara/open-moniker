import { Container, Typography } from "@mui/material";
import DomainGrid from "@/components/DomainGrid";
import PageTitle from "@/components/PageTitle";
import { getCatalogData, datasetCountForDomain } from "@/lib/data-loader";

export default function DomainsPage() {
  const data = getCatalogData();

  const domains = data.domains.map((d) => ({
    domainKey: d.key,
    displayName: d.display_name,
    notes: d.notes,
    color: d.color,
    dataCategory: d.data_category,
    datasetCount: datasetCountForDomain(data, d.key),
    confidentiality: d.confidentiality,
  }));

  return (
    <>
      <PageTitle title="Domains" />
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Typography variant="h4" sx={{ mb: 2, color: "#022D5E" }}>
          Domains
        </Typography>
        <DomainGrid domains={domains} />
      </Container>
    </>
  );
}
