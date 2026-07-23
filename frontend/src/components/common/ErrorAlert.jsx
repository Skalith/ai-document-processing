import Alert from "@mui/material/Alert";

export default function ErrorAlert({ message, onClose, sx }) {
  if (!message) return null;
  return (
    <Alert severity="error" onClose={onClose} sx={sx}>
      {message}
    </Alert>
  );
}
