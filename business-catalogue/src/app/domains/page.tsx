import { Container } from "@mui/material";
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
    owner: d.owner,
  }));

  return (
    <>
      <PageTitle title="Domains" />
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <DomainGrid domains={domains} />
      </Container>
    </>
  );
}
