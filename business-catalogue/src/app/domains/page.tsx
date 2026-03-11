import { Container } from "@mui/material";
import DomainGrid from "@/components/DomainGrid";
import PageTitle from "@/components/PageTitle";
import { fetchDomains, fetchNodes } from "@/lib/api-client";

export default async function DomainsPage() {
  const [domainsRes, nodesRes] = await Promise.all([
    fetchDomains(),
    fetchNodes(),
  ]);

  // Count leaf datasets per domain (prefix matching)
  const domainKeys = domainsRes.domains.map((d) => d.name);
  const datasetCounts = new Map<string, number>();
  for (const node of nodesRes.nodes) {
    if (!node.is_leaf) continue;
    const dk = domainKeys.find(
      (k) => node.path === k || node.path.startsWith(k + ".") || node.path.startsWith(k + "/")
    );
    if (dk) {
      datasetCounts.set(dk, (datasetCounts.get(dk) || 0) + 1);
    }
  }

  const domains = domainsRes.domains.map((d) => ({
    domainKey: d.name,
    displayName: d.display_name,
    notes: d.notes,
    color: d.color,
    dataCategory: d.data_category,
    datasetCount: datasetCounts.get(d.name) || 0,
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
