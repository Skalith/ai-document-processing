import Backdrop from "@mui/material/Backdrop";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import StopCircleRoundedIcon from "@mui/icons-material/StopCircleRounded";

/**
 * Full-screen overlay shown while an extraction job is running.
 * Displays the live progress percentage, the current pipeline stage,
 * and a Stop button so the user can cancel a long-running job.
 */
export default function ProcessingProgress({
  progress = 0,
  stage = "Processing…",
  cancelling = false,
  onCancel,
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(progress)));
  const showStopButton = !cancelling && typeof onCancel === "function";

  return (
    <Backdrop
      open
      sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: "rgba(0, 0, 0, 0.7)" }}
    >
      <Paper
        elevation={24}
        sx={{
          p: { xs: 3, sm: 4 },
          width: { xs: "90%", sm: 460 },
          textAlign: "center",
          borderRadius: 3,
        }}
      >
        <Typography variant="overline" color="primary.main">
          DocExtract
        </Typography>
        <Typography variant="h6" sx={{ mb: 3 }}>
          {stage}
        </Typography>

        <Box sx={{ width: "100%", mb: 1 }}>
          <LinearProgress
            variant="determinate"
            value={clamped}
            sx={{ height: 10, borderRadius: 5 }}
          />
        </Box>
        <Typography variant="h5" sx={{ mb: 1 }}>
          {clamped}%
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Keep this tab open while extraction runs. You can stop it any time.
        </Typography>

        {showStopButton && (
          <Button
            variant="outlined"
            color="error"
            size="large"
            fullWidth
            startIcon={<StopCircleRoundedIcon />}
            onClick={onCancel}
            sx={{ py: 1 }}
          >
            Stop extraction
          </Button>
        )}
        {cancelling && (
          <Typography variant="body2" color="warning.main">
            Stopping… this may take a moment.
          </Typography>
        )}
      </Paper>
    </Backdrop>
  );
}