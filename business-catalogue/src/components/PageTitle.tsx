import { Box, Typography } from "@mui/material";

export default function PageTitle({ title }: { title: string }) {
  return (
    <Box
      sx={{
        bgcolor: "#e9ecef",
        px: 3,
        py: 1,
      }}
    >
      <Typography
        variant="body2"
        sx={{ fontWeight: 700, textTransform: "uppercase" }}
      >
        {title}
      </Typography>
    </Box>
  );
}
