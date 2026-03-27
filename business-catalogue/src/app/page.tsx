import CatalogBrowser from "@/components/CatalogBrowser";
import PageTitle from "@/components/PageTitle";
import { loadBrowseDatasets } from "@/lib/load-datasets";

const INITIAL_BATCH = 50;

export default async function HomePage() {
  const initial = await loadBrowseDatasets(INITIAL_BATCH);
  return (
    <>
      <PageTitle title="Datasets" />
      <CatalogBrowser
        initialDatasets={initial.datasets}
        initialDomains={initial.domains}
        totalHint={initial.total}
      />
    </>
  );
}
