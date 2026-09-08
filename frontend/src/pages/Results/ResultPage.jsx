import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import DownloadRoundedIcon from "@mui/icons-material/DownloadRounded";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";

import OriginalDocumentViewer from "../../components/ResultsViewer/OriginalDocumentViewer";
import ExtractedOutputViewer from "../../components/ResultsViewer/ExtractedOutputViewer";
import ThemeButton from "../../components/Theme/ThemeButton";
import { useExtraction } from "../../context/ExtractionContext";
import { resolveFileUrl, resolveDownloadUrl } from "../../services/api";
import { OCR_ENGINES, DOCUMENT_TYPE_LABELS } from "../../utils/constants";

export default function ResultPage() {
  const navigate = useNavigate();
  const { session, clearSession } = useExtraction();

  if (!session) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          bgcolor: "background.default",
        }}
      >
        <Stack spacing={2} alignItems="center">
          <Typography variant="h6">No extraction result to show</Typography>
          <Typography variant="body2" color="text.secondary">
            Upload a document first to see results here.
          </Typography>
          <Button variant="contained" onClick={() => navigate("/")}>
            Go to upload
          </Button>
        </Stack>
      </Box>
    );
  }

  const { upload, extraction } = session;
  const fileUrl = resolveFileUrl(upload.file_url);
  const downloadUrl = resolveDownloadUrl(extraction.download_url);
  const ocrEngineLabel =
    OCR_ENGINES.find((e) => e.value === extraction.ocr_engine)?.label || extraction.ocr_engine;
  const documentTypeLabel = extraction.document_type
    ? DOCUMENT_TYPE_LABELS[extraction.document_type] || extraction.document_type
    : null;

  const handleNewExtraction = () => {
    clearSession();
    navigate("/");
  };

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column", bgcolor: "background.default" }}>
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{
          px: { xs: 2, md: 3 },
          py: 1.5,
          borderBottom: "1px solid",
          borderColor: "divider",
          bgcolor: "background.paper",
          flexWrap: "wrap",
          rowGap: 1,
        }}
      >
        <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" rowGap={1}>
          <Button
            startIcon={<ArrowBackRoundedIcon />}
            onClick={handleNewExtraction}
            size="small"
          >
            New extraction
          </Button>
          <Divider orientation="vertical" flexItem />
          <Chip label={ocrEngineLabel} size="small" variant="outlined" />
          {documentTypeLabel && (
            <Chip
              icon={<AutoAwesomeRoundedIcon />}
              label={documentTypeLabel}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
          <Chip
            label={extraction.status}
            size="small"
            variant="outlined"
            color={extraction.status === "completed" ? "success" : "default"}
          />
          <Chip label={`${extraction.processing_time_seconds}s`} size="small" variant="outlined" />
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center">
          <ThemeButton />
          <Button
            variant="outlined"
            size="small"
            startIcon={<DownloadRoundedIcon />}
            component="a"
            href={downloadUrl}
            download
          >
            Download output
          </Button>
        </Stack>
      </Stack>

      <Box
        sx={{
          flexGrow: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: { xs: "column", md: "row" },
        }}
      >
        <Box
          sx={{
            width: { xs: "100%", md: "50%" },
            height: { xs: "50%", md: "100%" },
            borderRight: { md: "1px solid" },
            borderBottom: { xs: "1px solid", md: 0 },
            borderColor: "divider",
          }}
        >
          <OriginalDocumentViewer
            fileUrl={fileUrl}
            contentType={upload.content_type}
            filename={upload.original_filename}
          />
        </Box>

        <Box sx={{ width: { xs: "100%", md: "50%" }, height: { xs: "50%", md: "100%" } }}>
          <ExtractedOutputViewer
            outputFormat={extraction.output_format}
            formattedOutput={extraction.formatted_output}
            ocrEngine={extraction.ocr_engine}
            documentType={extraction.document_type}
            usedStructuredExtraction={extraction.used_structured_extraction}
          />
        </Box>
      </Box>
    </Box>
  );
}
