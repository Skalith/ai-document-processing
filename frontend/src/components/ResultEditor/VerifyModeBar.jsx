import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import EditRoundedIcon from "@mui/icons-material/EditRounded";

// Header bar shown while the human-verification edit mode is active on the
// right pane. Gives the user Save (persist edits) / Cancel (discard) and a
// live count of fields changed so far.
export default function VerifyModeBar({ changeCount, onSave, onCancel }) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="space-between"
      sx={{ px: 2, py: 1, borderBottom: "1px solid", borderColor: "divider", bgcolor: "warning.light" }}
    >
      <Stack direction="row" spacing={1} alignItems="center">
        <EditRoundedIcon fontSize="small" color="warning" />
        <Typography variant="body2" fontWeight={600}>
          Editing Mode
        </Typography>
        <Chip
          label={`${changeCount} field${changeCount === 1 ? "" : "s"} edited`}
          size="small"
          variant="outlined"
          color="warning"
          sx={{ height: 20, fontSize: 11 }}
        />
      </Stack>

      <Stack direction="row" spacing={1}>
        <Button size="small" onClick={onCancel}>
          Cancel
        </Button>
        <Button size="small" variant="contained" color="warning" onClick={onSave}>
          Save Changes
        </Button>
      </Stack>
    </Stack>
  );
}