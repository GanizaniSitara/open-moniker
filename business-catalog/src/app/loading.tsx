import { Container, Box, Skeleton } from "@mui/material";

export default function Loading() {
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ display: "flex", gap: 4 }}>
        {/* Sidebar skeleton */}
        <Box sx={{ width: 240, flexShrink: 0, display: { xs: "none", md: "block" } }}>
          <Skeleton variant="text" width={100} height={28} sx={{ mb: 1 }} />
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} variant="text" width={160 + (i % 3) * 20} height={24} sx={{ mb: 0.5 }} />
          ))}
          <Skeleton variant="text" width={100} height={28} sx={{ mt: 2, mb: 1 }} />
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} variant="text" width={140} height={24} sx={{ mb: 0.5 }} />
          ))}
        </Box>

        {/* Main content skeleton */}
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Skeleton variant="rounded" width="100%" height={40} sx={{ mb: 2, borderRadius: 1 }} />
          <Skeleton variant="text" width={100} height={20} sx={{ mb: 2 }} />
          {Array.from({ length: 10 }, (_, i) => (
            <Box key={i} sx={{ py: 1.5 }}>
              <Box sx={{ display: "flex", alignItems: "center", mb: 0.3 }}>
                <Skeleton variant="text" width={180 + (i % 3) * 60} height={28} />
                <Box sx={{ flexGrow: 1 }} />
                <Skeleton variant="rounded" width={70} height={22} sx={{ borderRadius: "16px", mr: 0.5 }} />
                <Skeleton variant="rounded" width={55} height={22} sx={{ borderRadius: "16px" }} />
              </Box>
              <Skeleton variant="text" width="85%" height={20} />
            </Box>
          ))}
        </Box>
      </Box>
    </Container>
  );
}
