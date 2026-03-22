"use client";
import { Typography, Box, Paper, LinearProgress } from "@mui/material";
import { TechnicalProfile } from "@/lib/tech-catalogue-types";

interface Props {
  techDebt: TechnicalProfile["tech_debt"];
}

export default function TechDebtSection({ techDebt }: Props) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
        Tech Debt
      </Typography>
      <Paper variant="outlined" sx={{ p: 2 }}>
        {/* Score bars */}
        <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap", mb: 2 }}>
          <Box sx={{ flex: 1, minWidth: 200 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Debt Score
              </Typography>
              <Typography variant="body2" sx={{ color: "#53565A" }}>
                {techDebt.score}/100
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={techDebt.score}
              sx={{
                height: 10,
                borderRadius: 5,
                bgcolor: "#e9ecef",
                "& .MuiLinearProgress-bar": {
                  bgcolor:
                    techDebt.score > 60
                      ? "#D0002B"
                      : techDebt.score > 35
                      ? "#FFD100"
                      : "#009639",
                  borderRadius: 5,
                },
              }}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 200 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Modernization Score
              </Typography>
              <Typography variant="body2" sx={{ color: "#53565A" }}>
                {techDebt.modernization_score}/100
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={techDebt.modernization_score}
              sx={{
                height: 10,
                borderRadius: 5,
                bgcolor: "#e9ecef",
                "& .MuiLinearProgress-bar": {
                  bgcolor:
                    techDebt.modernization_score >= 70
                      ? "#009639"
                      : techDebt.modernization_score >= 40
                      ? "#FFD100"
                      : "#D0002B",
                  borderRadius: 5,
                },
              }}
            />
          </Box>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
          Last assessed: {techDebt.last_assessed}
        </Typography>

        {techDebt.migration_target && (
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Migration target:</strong> {techDebt.migration_target}
          </Typography>
        )}

        {techDebt.notes.length > 0 && (
          <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
            {techDebt.notes.map((note, i) => (
              <Typography component="li" variant="body2" key={i} sx={{ color: "#53565A", mb: 0.3 }}>
                {note}
              </Typography>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
}
