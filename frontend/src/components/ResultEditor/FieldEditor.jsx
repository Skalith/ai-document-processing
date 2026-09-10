import { useState } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Button from "@mui/material/Button";
import Collapse from "@mui/material/Collapse";
import ExpandMoreRoundedIcon from "@mui/icons-material/ExpandMoreRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";

import { isPlainObject } from "./changeTracker";

// Recursive, type-aware form for editing structured_data. Emits edits as
// (dottedPath, newValue) — the parent owns the data copy and applies them.
//
//  value    : node being edited (scalar | object | array)
//  aiValue  : matching node from the immutable AI result (AI hints + ✏️ chip)
//  path     : dotted path, e.g. "", "invoice_number", "line_items[0].amount"
//  onEdit   : (path, newValue) => void

function format(v) {
  if (v === null || v === undefined) return "";
  return String(v);
}

function inputType(value, aiValue) {
  const probe = value ?? aiValue;
  if (typeof probe === "number") return "number";
  return "string";
}

function AiHint({ aiValue }) {
  if (aiValue === null || aiValue === undefined) return null;
  const shown = format(aiValue);
  if (shown === "") return null;
  return (
    <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.25 }}>
      AI: {shown}
    </Typography>
  );
}

function ScalarField({ label, value, aiValue, showEdited, onChange }) {
  const type = inputType(value, aiValue);
  const edited = showEdited && format(value) !== format(aiValue);

  return (
    <Stack spacing={0.5}>
      <Stack direction="row" alignItems="center" spacing={1}>
        <Typography variant="body2" fontWeight={600} sx={{ flex: 1 }}>
          {label}
        </Typography>
        {edited && (
          <Chip label="✏️ Edited" size="small" color="warning" sx={{ height: 20, fontSize: 11 }} />
        )}
      </Stack>
      <TextField
        size="small"
        fullWidth
        type={type === "number" ? "number" : "text"}
        value={format(value)}
        placeholder={type === "number" ? "0" : "—"}
        onChange={(e) => {
          const raw = e.target.value;
          if (type === "number") {
            if (raw === "") return onChange(null);
            const num = Number(raw);
            return onChange(Number.isNaN(num) ? null : num);
          }
          onChange(raw);
        }}
      />
      <AiHint aiValue={aiValue} />
    </Stack>
  );
}

function templateFor(first) {
  if (first === undefined) return {};
  if (Array.isArray(first)) return [];
  if (isPlainObject(first)) {
    return Object.fromEntries(
      Object.keys(first).map((key) => [
        key,
        Array.isArray(first[key]) ? [] : first[key] === null ? null : "",
      ])
    );
  }
  return "";
}

function CollectionField({ label, items, aiItems, onEdit, path, itemLabel }) {
  const [open, setOpen] = useState(() => items.map(() => true));
  const toggleOpen = (i) =>
    setOpen((prev) => {
      const copy = [...prev];
      copy[i] = !copy[i];
      return copy;
    });

  return (
    <Box sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1.5, p: 1.5 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="subtitle2" fontWeight={600}>
          {label}
        </Typography>
        <Button
          size="small"
          startIcon={<AddRoundedIcon />}
          onClick={() => onEdit(path, [...items, templateFor(items[0])])}
        >
          Add
        </Button>
      </Stack>

      {items.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No {label} items — use "Add" above.
        </Typography>
      ) : (
        <Stack spacing={1}>
          {items.map((item, index) => {
            const isOpen = open[index] !== false;
            const aiItem = aiItems?.[index];
            const itemPath = path;
            const labelText = itemLabel ? itemLabel(item, index) : null;
            return (
              <Box key={index} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1, p: 1 }}>
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <IconButton size="small" onClick={() => toggleOpen(index)}>
                    {isOpen ? <ExpandMoreRoundedIcon /> : <ChevronRightRoundedIcon />}
                  </IconButton>
                  <Typography variant="body2" sx={{ flex: 1 }} color="text.secondary">
                    {labelText || `${label} ${index + 1}`}
                  </Typography>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => onEdit(path, items.filter((_, i) => i !== index))}
                  >
                    <DeleteOutlineRoundedIcon fontSize="small" />
                  </IconButton>
                </Stack>
                <Collapse in={isOpen}>
                  <Box sx={{ mt: 1 }}>
                    <FieldEditor
                      value={item}
                      aiValue={aiItem}
                      path={`${itemPath}[${index}]`}
                      onEdit={onEdit}
                    />
                  </Box>
                </Collapse>
              </Box>
            );
          })}
        </Stack>
      )}
    </Box>
  );
}

export default function FieldEditor({ value, aiValue, path = "", onEdit }) {
  if (Array.isArray(value)) {
    return (
      <CollectionField
        label={path || "Items"}
        items={value}
        aiItems={Array.isArray(aiValue) ? aiValue : []}
        onEdit={onEdit}
        path={path}
        itemLabel={(item) => {
          if (isPlainObject(item)) {
            const readable = Object.keys(item).find(
              (k) => item[k] !== "" && item[k] != null && typeof item[k] !== "object"
            );
            if (readable) return String(item[readable]);
          }
          return null;
        }}
      />
    );
  }

  if (isPlainObject(value)) {
    return (
      <Stack spacing={1.5}>
        {Object.keys(value).map((key) => {
          const childPath = path ? `${path}.${key}` : key;
          return (
            <FieldEditor
              key={childPath}
              value={value[key]}
              aiValue={aiValue?.[key]}
              path={childPath}
              onEdit={onEdit}
            />
          );
        })}
      </Stack>
    );
  }

  return (
    <ScalarField
      label={path || "(field)"}
      value={value}
      aiValue={aiValue}
      showEdited={aiValue !== undefined}
      onChange={(next) => onEdit(path, next)}
    />
  );
}