import { Suspense } from "react";
import CatalogBrowser from "@/components/CatalogBrowser";
import PageTitle from "@/components/PageTitle";

export default function DatasetsPage() {
  return (
    <>
      <PageTitle title="Datasets" />
      <Suspense>
        <CatalogBrowser />
      </Suspense>
    </>
  );
}
