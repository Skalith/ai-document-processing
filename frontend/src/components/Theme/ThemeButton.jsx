import { useState } from "react";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import CheckRoundedIcon from "@mui/icons-material/CheckRounded";
import PaletteRoundedIcon from "@mui/icons-material/PaletteRounded";

import { THEME_OPTIONS } from "../../theme";
import { useThemePreference } from "../../context/ThemeContext";

/**
 * Small "Theme" button that opens a dropdown with the 7 built-in themes.
 * Clicking any option applies it instantly and persists it to
 * localStorage (see ThemeContext.jsx).
 */
export default function ThemeButton() {
  const { themeId, setThemeId } = useThemePreference();
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleSelect = (id) => {
    setThemeId(id);
    setAnchorEl(null);
  };

  return (
    <>
      <Tooltip title="Theme">
        <IconButton
          onClick={(event) => setAnchorEl(event.currentTarget)}
          aria-label="Choose theme"
          size="small"
          sx={{ border: "1px solid", borderColor: "divider" }}
        >
          <PaletteRoundedIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        PaperProps={{ sx: { minWidth: 220, mt: 1 } }}
      >
        {THEME_OPTIONS.map(({ id, label, icon }) => {
          const selected = id === themeId;
          return (
            <MenuItem key={id} selected={selected} onClick={() => handleSelect(id)}>
              <Box
                component="span"
                sx={{ mr: 1.5, fontSize: 18, lineHeight: 1 }}
                aria-hidden="true"
              >
                {icon}
              </Box>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                {label}
              </Typography>
              {selected && <CheckRoundedIcon fontSize="small" color="primary" />}
            </MenuItem>
          );
        })}
      </Menu>
    </>
  );
}