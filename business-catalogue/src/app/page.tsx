import CatalogBrowser from "@/components/CatalogBrowser";
import PageTitle from "@/components/PageTitle";

export default function HomePage() {
  return (
    <>
      <PageTitle title="Datasets" />
      <CatalogBrowser />
    </>
  );
}
