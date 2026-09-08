import { createTheme } from "@mui/material/styles";

// Design language: "light table" — the surface a document sits on to be
// scanned. A cool graphite ground, a warm paper card for the document
// itself, and a single scanner-beam teal used sparingly for action and
// progress states.
//
// The app ships with 7 selectable themes (see THEMES below). Every theme
// is just a MUI palette (+ optional component overrides), so nothing else
// in the UI needs to know about theming. `getTheme(id)` builds a full MUI
// theme from a definition, and a selection is persisted to localStorage
// by the ThemePreferenceProvider (context/ThemeContext.jsx).

const SHAPE = { borderRadius: 10 };

const TYPOGRAPHY = {
  fontFamily: '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
  h1: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 700 },
  h2: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 700 },
  h3: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
  h4: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
  h5: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
  h6: { fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600 },
  button: { textTransform: "none", fontWeight: 600 },
  overline: {
    fontFamily: '"IBM Plex Mono", monospace',
    letterSpacing: "0.08em",
  },
};

const BASE_COMPONENTS = {
  MuiButton: {
    styleOverrides: {
      root: { borderRadius: 8, paddingInline: 20 },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: { backgroundImage: "none" },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: { fontWeight: 600 },
    },
  },
};

const GLASS_PAPER = {
  backgroundColor: "rgba(255,255,255,0.16)",
  backdropFilter: "blur(14px)",
  WebkitBackdropFilter: "blur(14px)",
  border: "1px solid rgba(255,255,255,0.3)",
  boxShadow: "0 8px 32px rgba(0,0,0,0.28)",
  color: "#FFFFFF",
  backgroundImage: "none",
};

export const THEMES = [
  {
    id: "obsidian-dark",
    label: "Obsidian Dark",
    icon: "🌑",
    palette: {
      mode: "dark",
      background: { default: "#0B0E13", paper: "#151B23" },
      primary: { main: "#1DB0B3", dark: "#17898B", contrastText: "#FFFFFF" },
      secondary: { main: "#E8A24F", contrastText: "#0B0E13" },
      text: { primary: "#E7EAF0", secondary: "#9CA8B8" },
      divider: "#232B36",
      error: { main: "#EF5B5B" },
    },
  },
  {
    id: "clean-light",
    label: "Clean Light",
    icon: "☀️",
    palette: {
      mode: "light",
      background: { default: "#F5F6F8", paper: "#FFFFFF" },
      primary: { main: "#0F8B8D", dark: "#0B6C6E", contrastText: "#FFFFFF" },
      secondary: { main: "#C97A2B", contrastText: "#FFFFFF" },
      text: { primary: "#12161C", secondary: "#3A4250" },
      divider: "#E1E4E9",
      error: { main: "#C13B3B" },
    },
  },
  {
    id: "midnight-aurora",
    label: "Midnight Aurora",
    icon: "🌌",
    palette: {
      mode: "dark",
      background: { default: "#0A0E1F", paper: "#141A33" },
      primary: { main: "#8B7BFF", dark: "#6A5CE0", contrastText: "#FFFFFF" },
      secondary: { main: "#4ED99A", contrastText: "#0A0E1F" },
      text: { primary: "#E8E7FF", secondary: "#A9A6D8" },
      divider: "#232A4A",
      error: { main: "#F26D8D" },
    },
  },
  {
    id: "glassmorphism",
    label: "Glassmorphism",
    icon: "💎",
    palette: {
      mode: "light",
      background: {
        default: "linear-gradient(135deg, #6D5DF6 0%, #8553D8 45%, #2F6BFF 100%)",
        paper: "rgba(255,255,255,0.16)",
      },
      primary: { main: "#FFE27D", dark: "#E6C154", contrastText: "#1B1B2F" },
      secondary: { main: "#7CFFCB", contrastText: "#1B1B2F" },
      text: { primary: "#FFFFFF", secondary: "rgba(255,255,255,0.82)" },
      divider: "rgba(255,255,255,0.28)",
      error: { main: "#FF8FA3" },
    },
    components: {
      MuiPaper: { styleOverrides: { root: GLASS_PAPER } },
    },
  },
  {
    id: "ocean-blue",
    label: "Ocean Blue",
    icon: "🌊",
    palette: {
      mode: "light",
      background: { default: "#EEF4FB", paper: "#FFFFFF" },
      primary: { main: "#1F6FEB", dark: "#1858C4", contrastText: "#FFFFFF" },
      secondary: { main: "#0EA5A0", contrastText: "#FFFFFF" },
      text: { primary: "#0F2740", secondary: "#4E6B85" },
      divider: "#D8E3F0",
      error: { main: "#D64545" },
    },
  },
  {
    id: "emerald",
    label: "Emerald",
    icon: "🌿",
    palette: {
      mode: "light",
      background: { default: "#F1F7F2", paper: "#FFFFFF" },
      primary: { main: "#1F9D6B", dark: "#177A54", contrastText: "#FFFFFF" },
      secondary: { main: "#C9971C", contrastText: "#FFFFFF" },
      text: { primary: "#14351F", secondary: "#4C6B58" },
      divider: "#D6E7DA",
      error: { main: "#C4503E" },
    },
  },
  {
    id: "sunset",
    label: "Sunset",
    icon: "🌅",
    palette: {
      mode: "light",
      background: { default: "#FFF4EC", paper: "#FFFFFF" },
      primary: { main: "#E07B39", dark: "#C05F27", contrastText: "#FFFFFF" },
      secondary: { main: "#D45D7A", contrastText: "#FFFFFF" },
      text: { primary: "#3B2B22", secondary: "#7A6A5F" },
      divider: "#F0DED1",
      error: { main: "#C14032" },
    },
  },
];

export const THEME_OPTIONS = THEMES.map(({ id, label, icon }) => ({
  id,
  label,
  icon,
}));

export const DEFAULT_THEME_ID = "clean-light";

export function getTheme(themeId) {
  const definition = THEMES.find((theme) => theme.id === themeId) || THEMES[0];
  return createTheme({
    palette: definition.palette,
    shape: SHAPE,
    typography: TYPOGRAPHY,
    components: {
      ...BASE_COMPONENTS,
      ...(definition.components || {}),
    },
  });
}

// Kept for compatibility with any existing `import { theme }` consumers.
export const theme = getTheme(DEFAULT_THEME_ID);