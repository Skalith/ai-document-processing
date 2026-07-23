import { createTheme } from "@mui/material/styles";

// Design language: "light table" — the surface a document sits on to be
// scanned. A cool graphite ground, a warm paper card for the document
// itself, and a single scanner-beam teal used sparingly for action and
// progress states.
const paper = "#FFFFFF";
const ground = "#F5F6F8";
const ink = "#12161C";
const graphite = "#3A4250";
const beam = "#0F8B8D"; // scanner-line teal, the one accent
const beamDark = "#0B6C6E";
const amber = "#C97A2B"; // used only for the PDF/warning-adjacent states

export const theme = createTheme({
  palette: {
    mode: "light",
    background: { default: ground, paper },
    primary: { main: beam, dark: beamDark, contrastText: "#FFFFFF" },
    secondary: { main: amber, contrastText: "#FFFFFF" },
    text: { primary: ink, secondary: graphite },
    divider: "#E1E4E9",
    error: { main: "#C13B3B" },
  },
  shape: { borderRadius: 10 },
  typography: {
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
  },
  components: {
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
  },
});
