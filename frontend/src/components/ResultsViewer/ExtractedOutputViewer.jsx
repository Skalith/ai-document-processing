import { useState } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Chip from "@mui/material/Chip";
import ReactMarkdown from "react-markdown";
import { DOCUMENT_TYPE_LABELS } from "../../utils/constants";

const FORMAT_LABELS = {
  markdown: "Markdown",
  html: "HTML",
  json: "JSON",
};

export default function ExtractedOutputViewer({
  outputFormat,
  formattedOutput,
  ocrEngine,
  documentType,
  usedStructuredExtraction,
}) {
  // Markdown and HTML can be viewed either rendered or as the raw text the
  // backend produced. JSON has no separate "rendered" mode — the formatted,
  // pretty-printed string from the backend IS the display form.
  const supportsToggle = outputFormat === "markdown" || outputFormat === "html";
  const [viewMode, setViewMode] = useState("preview"); // "preview" | "raw"
  const documentTypeLabel = documentType
    ? DOCUMENT_TYPE_LABELS[documentType] || documentType
    : null;

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ px: 2, py: 1.5, borderBottom: "1px solid", borderColor: "divider" }}
      >
        <Box>
          <Typography variant="overline" color="text.secondary">
            Extracted output
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" rowGap={0.5}>
            <Typography variant="body2" fontWeight={600}>
              {FORMAT_LABELS[outputFormat] || outputFormat}
            </Typography>
            {ocrEngine && (
              <Chip label={ocrEngine} size="small" variant="outlined" sx={{ height: 20 }} />
            )}
            {documentTypeLabel && (
              <Chip
                label={
                  usedStructuredExtraction
                    ? `${documentTypeLabel} · structured`
                    : documentTypeLabel
                }
                size="small"
                color="primary"
                variant="outlined"
                sx={{ height: 20 }}
              />
            )}
          </Stack>
        </Box>

        {supportsToggle && (
          <ToggleButtonGroup
            size="small"
            exclusive
            value={viewMode}
            onChange={(_, next) => next && setViewMode(next)}
          >
            <ToggleButton value="preview">Preview</ToggleButton>
            <ToggleButton value="raw">Raw</ToggleButton>
          </ToggleButtonGroup>
        )}
      </Stack>

      <Box sx={{ flexGrow: 1, minHeight: 0, overflow: "auto", bgcolor: "background.paper" }}>
        {outputFormat === "json" && (
          <Box
            component="pre"
            sx={{
              m: 0,
              p: 2.5,
              fontFamily: '"IBM Plex Mono", monospace',
              fontSize: 13,
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {formattedOutput}
          </Box>
        )}

        {outputFormat === "html" && viewMode === "preview" && (
          <Box
            component="iframe"
            title="Extracted HTML output"
            srcDoc={formattedOutput}
            sx={{ width: "100%", height: "100%", border: 0, bgcolor: "#fff" }}
          />
        )}

        {outputFormat === "html" && viewMode === "raw" && (
          <Box
            component="pre"
            sx={{
              m: 0,
              p: 2.5,
              fontFamily: '"IBM Plex Mono", monospace',
              fontSize: 13,
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {formattedOutput}
          </Box>
        )}

        {outputFormat === "markdown" && viewMode === "preview" && (
          <Box
            sx={{
              p: 2.5,
              "& h2": { fontFamily: '"Space Grotesk", sans-serif' },
              "& pre": { bgcolor: "#F5F6F8", p: 1.5, borderRadius: 1, overflow: "auto" },
              "& table": { borderCollapse: "collapse", width: "100%" },
              "& th, & td": { border: "1px solid #E1E4E9", p: 1 },
            }}
          >
            <ReactMarkdown>{formattedOutput}</ReactMarkdown>
          </Box>
        )}

        {outputFormat === "markdown" && viewMode === "raw" && (
          <Box
            component="pre"
            sx={{
              m: 0,
              p: 2.5,
              fontFamily: '"IBM Plex Mono", monospace',
              fontSize: 13,
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {formattedOutput}
          </Box>
        )}
      </Box>
    </Box>
  );
}
