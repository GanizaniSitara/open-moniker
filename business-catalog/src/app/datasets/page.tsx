import { Suspense } from "react";
import CatalogBrowser from "@/components/CatalogBrowser";
import PageTitle from "@/components/PageTitle";
import { loadBrowseDatasets } from "@/lib/load-datasets";

const INITIAL_BATCH = 50;

export default async function DatasetsPage() {
  const initial = await loadBrowseDatasets(INITIAL_BATCH);
  return (
    <>
      <PageTitle title="Datasets" />
      <Suspense>
        <CatalogBrowser
          initialDatasets={initial.datasets}
          initialDomains={initial.domains}
          totalHint={initial.total}
        />
      </Suspense>
    </>
  );
}
