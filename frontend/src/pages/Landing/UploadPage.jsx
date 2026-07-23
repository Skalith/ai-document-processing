import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Container from "@mui/material/Container";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";

import FileUploadBox from "../../components/FileUpload/FileUploadBox";
import ErrorAlert from "../../components/common/ErrorAlert";
import { OCR_ENGINES, OUTPUT_FORMATS } from "../../utils/constants";
import { uploadDocument, extractDocument, getErrorMessage } from "../../services/api";
import { useExtraction } from "../../context/ExtractionContext";

export default function UploadPage() {
  const navigate = useNavigate();
  const { setSession } = useExtraction();

  const [file, setFile] = useState(null);
  const [ocrEngine, setOcrEngine] = useState("tesseract");
  const [outputFormat, setOutputFormat] = useState("markdown");
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusLabel, setStatusLabel] = useState("");
  const [error, setError] = useState("");

  const canExtract = Boolean(file) && !isProcessing;

  const handleExtract = async () => {
    if (!file) return;
    setError("");
    setIsProcessing(true);

    try {
      // Step 1: POST /api/upload
      setStatusLabel("Uploading document…");
      const uploadResponse = await uploadDocument(file);

      // Step 2: POST /api/extract with the file_id from the upload response
      setStatusLabel("Running OCR extraction…");
      const extractResponse = await extractDocument({
        fileId: uploadResponse.file_id,
        ocrEngine,
        outputFormat,
      });

      // Persist everything the Results page needs, then navigate.
      setSession({
        upload: uploadResponse,
        extraction: extractResponse,
        localFileType: file.type,
      });

      navigate("/result");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsProcessing(false);
      setStatusLabel("");
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default", py: { xs: 4, md: 8 } }}>
      <Container maxWidth="sm">
        <Stack spacing={0.5} sx={{ mb: 4 }}>
          <Typography variant="overline" color="primary.main">
            DocExtract
          </Typography>
          <Typography variant="h4">Upload a document</Typography>
          <Typography variant="body1" color="text.secondary">
            Choose an OCR engine and an output format, then extract.
          </Typography>
        </Stack>

        <Paper
          variant="outlined"
          sx={{ p: { xs: 2.5, md: 4 }, borderRadius: 3, borderColor: "divider" }}
        >
          <Stack spacing={3}>
            <FileUploadBox
              file={file}
              onFileSelected={(f) => {
                setError("");
                setFile(f);
              }}
              onFileRemoved={() => setFile(null)}
              disabled={isProcessing}
            />

            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <FormControl fullWidth disabled={isProcessing}>
                <InputLabel id="ocr-engine-label">OCR Engine</InputLabel>
                <Select
                  labelId="ocr-engine-label"
                  label="OCR Engine"
                  value={ocrEngine}
                  onChange={(e) => setOcrEngine(e.target.value)}
                >
                  {OCR_ENGINES.map((engine) => (
                    <MenuItem key={engine.value} value={engine.value}>
                      {engine.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth disabled={isProcessing}>
                <InputLabel id="output-format-label">Output Format</InputLabel>
                <Select
                  labelId="output-format-label"
                  label="Output Format"
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                >
                  {OUTPUT_FORMATS.map((format) => (
                    <MenuItem key={format.value} value={format.value}>
                      {format.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>

            <ErrorAlert message={error} onClose={() => setError("")} />

            <Button
              variant="contained"
              size="large"
              onClick={handleExtract}
              disabled={!canExtract}
              endIcon={
                isProcessing ? (
                  <CircularProgress size={18} color="inherit" />
                ) : (
                  <ArrowForwardRoundedIcon />
                )
              }
              sx={{ alignSelf: "flex-start", py: 1.25 }}
            >
              {isProcessing ? statusLabel || "Processing…" : "Extract"}
            </Button>
          </Stack>
        </Paper>
      </Container>
    </Box>
  );
}
