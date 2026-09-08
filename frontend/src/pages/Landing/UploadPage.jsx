import { useEffect, useRef, useState } from "react";
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
import ProcessingProgress from "../../components/Progress/ProcessingProgress";
import ThemeButton from "../../components/Theme/ThemeButton";
import { OCR_ENGINES, OUTPUT_FORMATS } from "../../utils/constants";
import {
  uploadDocument,
  startExtraction,
  getExtractionJob,
  cancelExtraction,
  getErrorMessage,
} from "../../services/api";
import { useExtraction } from "../../context/ExtractionContext";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// The backend job reports progress over the whole pipeline (0-100). The
// upload phase happens first and isn't part of that scale, so we map
// upload 0-15% and let the job's own progress fill the remaining 85%.
const UPLOAD_MAX = 15;

function scaleJobProgress(jobProgress) {
  return Math.min(100, UPLOAD_MAX + jobProgress * (100 - UPLOAD_MAX) / 100);
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { setSession } = useExtraction();

  const [file, setFile] = useState(null);
  const [ocrEngine, setOcrEngine] = useState("tesseract");
  const [outputFormat, setOutputFormat] = useState("markdown");
  const [phase, setPhase] = useState("idle"); // idle | uploading | processing | cancelling
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("");
  const [error, setError] = useState("");

  const mountedRef = useRef(true);
  const abortRef = useRef(false);
  const jobIdRef = useRef(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const busy = phase !== "idle";
  const canExtract = Boolean(file) && !busy;

  const handleExtract = async () => {
    if (!file) return;

    setError("");
    abortRef.current = false;
    jobIdRef.current = null;
    setPhase("uploading");
    setProgress(0);
    setStage("Uploading document…");

    let uploadResponse;

    try {
      // Step 1: POST /api/upload (with live upload percentage).
      uploadResponse = await uploadDocument(file, {
        onUploadProgress: (e) => {
          if (!e.total) return;
          setProgress(Math.min(UPLOAD_MAX, (e.loaded / e.total) * UPLOAD_MAX));
        },
      });
      if (!mountedRef.current || abortRef.current) return;

      setProgress(UPLOAD_MAX);
      setStage("Starting extraction…");

      // Step 2: POST /api/extract -> creates a background job, returns a job id.
      const job = await startExtraction({
        fileId: uploadResponse.file_id,
        ocrEngine,
        outputFormat,
      });
      if (!mountedRef.current || abortRef.current) return;

      jobIdRef.current = job.job_id;
      setPhase("processing");
      setProgress(scaleJobProgress(job.progress));
      setStage(job.stage);

      // Step 3: poll the job until it reaches a terminal state.
      while (mountedRef.current && !abortRef.current) {
        const snapshot = await getExtractionJob(job.job_id);
        if (!mountedRef.current || abortRef.current) return;

        setProgress(scaleJobProgress(snapshot.progress));
        setStage(snapshot.stage);

        if (snapshot.status === "completed") {
          setSession({
            upload: uploadResponse,
            extraction: snapshot.result,
            localFileType: file.type,
          });
          navigate("/result");
          return;
        }

        if (snapshot.status === "failed") {
          setError(snapshot.error || "Extraction failed. Please try again.");
          return;
        }

        if (snapshot.status === "cancelled") {
          setError("Extraction was cancelled.");
          return;
        }

        await sleep(800);
      }
    } catch (err) {
      if (mountedRef.current && !abortRef.current) {
        setError(getErrorMessage(err));
      }
    } finally {
      if (mountedRef.current) {
        if (abortRef.current) {
          setError("Extraction was cancelled.");
        }
        setPhase("idle");
        setProgress(0);
        setStage("");
        jobIdRef.current = null;
        abortRef.current = false;
      }
    }
  };

  const handleCancel = () => {
    abortRef.current = true;
    setPhase("cancelling");
    if (jobIdRef.current) {
      // Ask the backend to stop the job; polling loop aborts above.
      cancelExtraction(jobIdRef.current).catch(() => {});
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default", py: { xs: 4, md: 8 } }}>
      <Container maxWidth="sm">
        <Stack
          direction="row"
          alignItems="flex-start"
          justifyContent="space-between"
          sx={{ mb: 4 }}
        >
          <Stack spacing={0.5}>
            <Typography variant="overline" color="primary.main">
              DocExtract
            </Typography>
            <Typography variant="h4">Upload a document</Typography>
            <Typography variant="body1" color="text.secondary">
              Choose an OCR engine and an output format, then extract.
            </Typography>
          </Stack>
          <ThemeButton />
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
              disabled={busy}
            />

            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <FormControl fullWidth disabled={busy}>
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

              <FormControl fullWidth disabled={busy}>
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
                busy ? (
                  <CircularProgress size={18} color="inherit" />
                ) : (
                  <ArrowForwardRoundedIcon />
                )
              }
              sx={{ alignSelf: "flex-start", py: 1.25 }}
            >
              {busy ? "Processing…" : "Extract"}
            </Button>
          </Stack>
        </Paper>
      </Container>

      {busy && (
        <ProcessingProgress
          progress={progress}
          stage={stage}
          cancelling={phase === "cancelling"}
          onCancel={handleCancel}
        />
      )}
    </Box>
  );
}