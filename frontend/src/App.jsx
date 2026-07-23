import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";

import { theme } from "./theme";
import { ExtractionProvider } from "./context/ExtractionContext";
import UploadPage from "./pages/Landing/UploadPage";
import ResultPage from "./pages/Results/ResultPage";

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ExtractionProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/result" element={<ResultPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ExtractionProvider>
    </ThemeProvider>
  );
}
