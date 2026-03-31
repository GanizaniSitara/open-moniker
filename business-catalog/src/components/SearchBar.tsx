"use client";
import { useState, useEffect, useRef } from "react";
import {
  TextField,
  Paper,
  List,
  ListItemButton,
  ListItemText,
  Chip,
  Box,
  InputAdornment,
  ClickAwayListener,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { useRouter } from "next/navigation";
interface SearchResult {
  type: string;
  key: string;
  display_name: string;
  description?: string;
  url: string;
}

const TYPE_COLORS: Record<string, string> = {
  domain: "#00897B",
  dataset: "#005587",
  model: "#789D4A",
};

interface SearchBarProps {
  placeholder?: string;
  fullWidth?: boolean;
  size?: "small" | "medium";
}

export default function SearchBar({
  placeholder = "Search datasets, domains, fields...",
  fullWidth = false,
  size = "medium",
}: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/search?q=${encodeURIComponent(query.trim())}`
        );
        const data = await res.json();
        setResults(data.results || []);
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  return (
    <ClickAwayListener onClickAway={() => setOpen(false)}>
      <Box sx={{ position: "relative", width: fullWidth ? "100%" : 400 }}>
        <TextField
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          size={size}
          fullWidth
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            },
          }}
          sx={{
            bgcolor: "white",
            borderRadius: 1,
            "& .MuiOutlinedInput-root": {
              borderRadius: 1,
            },
          }}
          onFocus={() => results.length > 0 && setOpen(true)}
        />
        {open && results.length > 0 && (
          <Paper
            sx={{
              position: "absolute",
              top: "100%",
              left: 0,
              right: 0,
              zIndex: 1300,
              maxHeight: 400,
              overflow: "auto",
              mt: 0.5,
            }}
            elevation={4}
          >
            <List dense>
              {results.slice(0, 10).map((r) => (
                <ListItemButton
                  key={`${r.type}-${r.key}`}
                  onClick={() => {
                    setOpen(false);
                    setQuery("");
                    router.push(r.url);
                  }}
                >
                  <Chip
                    label={r.type}
                    size="small"
                    sx={{
                      mr: 1.5,
                      bgcolor: TYPE_COLORS[r.type] || "#666",
                      color: "white",
                      fontSize: "0.7rem",
                      height: 22,
                      minWidth: 60,
                    }}
                  />
                  <ListItemText
                    primary={r.display_name}
                    secondary={r.description}
                    secondaryTypographyProps={{
                      noWrap: true,
                      sx: { maxWidth: 300 },
                    }}
                  />
                </ListItemButton>
              ))}
            </List>
          </Paper>
        )}
      </Box>
    </ClickAwayListener>
  );
}
