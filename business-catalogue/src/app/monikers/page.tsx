import { Suspense } from "react";
import { Container, Box, CircularProgress } from "@mui/material";
import PageTitle from "@/components/PageTitle";
import MonikerTree from "@/components/MonikerTree";

export default function MonikersPage() {
  return (
    <>
      <PageTitle title="Monikers" />
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Suspense
          fallback={
            <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
              <CircularProgress />
            </Box>
          }
        >
          <MonikerTree />
        </Suspense>
      </Container>
    </>
  );
}
