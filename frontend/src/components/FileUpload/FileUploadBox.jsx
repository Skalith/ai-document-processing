import { useCallback, useRef, useState } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import Chip from "@mui/material/Chip";
import UploadFileRoundedIcon from "@mui/icons-material/UploadFileRounded";
import DescriptionRoundedIcon from "@mui/icons-material/DescriptionRounded";
import ImageRoundedIcon from "@mui/icons-material/ImageRounded";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import { ACCEPTED_EXTENSIONS, ACCEPTED_MIME_TYPES } from "../../utils/constants";
import { formatBytes } from "../../utils/formatBytes";

function isAccepted(file) {
  const ext = `.${file.name.split(".").pop().toLowerCase()}`;
  return (
    ACCEPTED_MIME_TYPES.includes(file.type) ||
    ACCEPTED_EXTENSIONS.includes(ext)
  );
}

export default function FileUploadBox({ file, onFileSelected, onFileRemoved, disabled }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [dragError, setDragError] = useState("");
  const inputRef = useRef(null);

  const handleFiles = useCallback(
    (fileList) => {
      const picked = fileList?.[0];
      if (!picked) return;
      if (!isAccepted(picked)) {
        setDragError("Only PDF, PNG, JPG or JPEG files are supported.");
        return;
      }
      setDragError("");
      onFileSelected(picked);
    },
    [onFileSelected]
  );

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragActive(false);
    if (disabled) return;
    handleFiles(event.dataTransfer.files);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    if (disabled) return;
    setIsDragActive(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragActive(false);
  };

  const handleClick = () => {
    if (disabled) return;
    inputRef.current?.click();
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleClick();
    }
  };

  if (file) {
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    return (
      <Box
        sx={{
          border: "1px solid",
          borderColor: "divider",
          borderRadius: 2,
          p: 2.5,
          bgcolor: "background.paper",
        }}
      >
        <Stack direction="row" alignItems="center" spacing={2}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 1.5,
              display: "grid",
              placeItems: "center",
              bgcolor: "rgba(15,139,141,0.1)",
              color: "primary.main",
              flexShrink: 0,
            }}
          >
            {isPdf ? <DescriptionRoundedIcon /> : <ImageRoundedIcon />}
          </Box>
          <Box sx={{ minWidth: 0, flexGrow: 1 }}>
            <Typography variant="body1" fontWeight={600} noWrap title={file.name}>
              {file.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatBytes(file.size)}
            </Typography>
          </Box>
          <IconButton
            aria-label="Remove file"
            onClick={onFileRemoved}
            disabled={disabled}
            size="small"
          >
            <CloseRoundedIcon fontSize="small" />
          </IconButton>
        </Stack>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        sx={{
          border: "2px dashed",
          borderColor: isDragActive ? "primary.main" : "divider",
          borderRadius: 2,
          p: 6,
          textAlign: "center",
          cursor: disabled ? "default" : "pointer",
          bgcolor: isDragActive ? "rgba(15,139,141,0.06)" : "background.paper",
          transition: "border-color 120ms ease, background-color 120ms ease",
          opacity: disabled ? 0.6 : 1,
          "&:focus-visible": {
            outline: "2px solid",
            outlineColor: "primary.main",
            outlineOffset: 2,
          },
        }}
      >
        <input
          ref={inputRef}
          type="file"
          hidden
          accept={ACCEPTED_MIME_TYPES.concat(ACCEPTED_EXTENSIONS).join(",")}
          onChange={(e) => handleFiles(e.target.files)}
          disabled={disabled}
        />
        <UploadFileRoundedIcon sx={{ fontSize: 40, color: "primary.main", mb: 1.5 }} />
        <Typography variant="body1" fontWeight={600}>
          Drag & drop a document here, or click to browse
        </Typography>
        <Stack direction="row" spacing={1} justifyContent="center" sx={{ mt: 1.5 }}>
          {["PDF", "PNG", "JPG", "JPEG"].map((ext) => (
            <Chip key={ext} label={ext} size="small" variant="outlined" />
          ))}
        </Stack>
      </Box>
      {dragError && (
        <Typography variant="body2" color="error" sx={{ mt: 1 }}>
          {dragError}
        </Typography>
      )}
    </Box>
  );
}
