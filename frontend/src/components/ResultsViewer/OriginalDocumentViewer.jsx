import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";

export default function OriginalDocumentViewer({ fileUrl, contentType, filename }) {
  const isPdf = contentType === "application/pdf" || filename?.toLowerCase().endsWith(".pdf");

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Stack sx={{ px: 2, py: 1.5, borderBottom: "1px solid", borderColor: "divider" }}>
        <Typography variant="overline" color="text.secondary">
          Original document
        </Typography>
        <Typography variant="body2" fontWeight={600} noWrap title={filename}>
          {filename}
        </Typography>
      </Stack>

      <Box sx={{ flexGrow: 1, minHeight: 0, bgcolor: "#EDEFF2" }}>
        {isPdf ? (
          <Box
            component="iframe"
            src={fileUrl}
            title={filename || "Original document"}
            sx={{ width: "100%", height: "100%", border: 0 }}
          />
        ) : (
          <Box
            sx={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              overflow: "auto",
              p: 2,
            }}
          >
            <Box
              component="img"
              src={fileUrl}
              alt={filename || "Original document"}
              sx={{ maxWidth: "100%", maxHeight: "100%", boxShadow: 2, borderRadius: 1 }}
            />
          </Box>
        )}
      </Box>
    </Box>
  );
}
