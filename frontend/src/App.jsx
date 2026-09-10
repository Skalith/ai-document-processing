import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";

import { getTheme } from "./theme";
import { ThemePreferenceProvider, useThemePreference } from "./context/ThemeContext";
import { ExtractionProvider } from "./context/ExtractionContext";
import { UserResultProvider } from "./context/UserResultContext";
import UploadPage from "./pages/Landing/UploadPage";
import ResultPage from "./pages/Results/ResultPage";

function AppContent() {
  const { themeId } = useThemePreference();

  return (
    <ThemeProvider theme={getTheme(themeId)}>
      <CssBaseline />
      <ExtractionProvider>
        <UserResultProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<UploadPage />} />
              <Route path="/result" element={<ResultPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </UserResultProvider>
      </ExtractionProvider>
    </ThemeProvider>
  );
}

export default function App() {
  return (
    <ThemePreferenceProvider>
      <AppContent />
    </ThemePreferenceProvider>
  );
}