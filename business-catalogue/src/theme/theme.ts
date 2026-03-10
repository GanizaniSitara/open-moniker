"use client";
import { createTheme } from "@mui/material/styles";

// Moss Tidal extended palette
declare module "@mui/material/styles" {
  interface Palette {
    moss: {
      navy: string;
      blue: string;
      olive: string;
      teal: string;
      gray: string;
      cerulean: string;
      denim: string;
      aqua: string;
      plum: string;
      wine: string;
      forest: string;
      glacier: string;
    };
  }
  interface PaletteOptions {
    moss?: {
      navy?: string;
      blue?: string;
      olive?: string;
      teal?: string;
      gray?: string;
      cerulean?: string;
      denim?: string;
      aqua?: string;
      plum?: string;
      wine?: string;
      forest?: string;
      glacier?: string;
    };
  }
}

const theme = createTheme({
  palette: {
    primary: {
      main: "#022D5E",
      light: "#005587",
      dark: "#011B3A",
    },
    secondary: {
      main: "#789D4A",
      light: "#93B468",
      dark: "#5E7B3A",
    },
    success: {
      main: "#009639",
    },
    warning: {
      main: "#FFD100",
    },
    error: {
      main: "#D0002B",
    },
    info: {
      main: "#008BCD",
    },
    background: {
      default: "#FFFFFF",
      paper: "#FFFFFF",
    },
    text: {
      primary: "#000000",
      secondary: "#53565A",
    },
    moss: {
      navy: "#022D5E",
      blue: "#005587",
      olive: "#789D4A",
      teal: "#00897B",
      gray: "#53565A",
      cerulean: "#008BCD",
      denim: "#36749D",
      aqua: "#00BFB3",
      plum: "#80276C",
      wine: "#621244",
      forest: "#215D25",
      glacier: "#6BA4B8",
    },
  },
  typography: {
    fontFamily: '"Arial", "Helvetica", sans-serif',
    h1: {
      fontSize: "2.5rem",
      fontWeight: 700,
    },
    h2: {
      fontSize: "2rem",
      fontWeight: 600,
    },
    h3: {
      fontSize: "1.5rem",
      fontWeight: 600,
    },
    h4: {
      fontSize: "1.25rem",
      fontWeight: 600,
    },
    h5: {
      fontSize: "1.1rem",
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "none",
          border: "1px solid rgba(83,86,90,0.35)",
          transition: "background-color 0.2s",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        outlined: {
          borderColor: "rgba(83,86,90,0.35)",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
  },
});

export default theme;
