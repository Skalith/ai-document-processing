// Mirrors backend/app/models/schemas.py enums exactly.
// Values (not just labels) are sent verbatim in the ExtractRequest body,
// so these strings must never drift from the backend Enum values.

export const OCR_ENGINES = [
  { value: "tesseract", label: "Tesseract OCR" },
  { value: "easyocr", label: "EasyOCR" },
  { value: "paddleocr", label: "PaddleOCR" },
  { value: "docling", label: "Docling OCR" },
];

export const OUTPUT_FORMATS = [
  { value: "markdown", label: "Markdown" },
  { value: "html", label: "HTML" },
  { value: "json", label: "JSON" },
];

// Mirrors backend/app/models/schemas.py DocumentType enum. Used to render
// a friendly label for the LLM-classified document type on the results
// page. `extraction.document_type` is null whenever the LLM pipeline was
// unavailable/failed and the backend fell back to plain OCR output.
export const DOCUMENT_TYPE_LABELS = {
  invoice: "Invoice",
  resume: "Resume",
  receipt: "Receipt",
  other: "Other",
};

// Accepted MIME types for the upload dropzone, per the product spec.
// (Backend also allows TIFF/BMP, but the UI intentionally only exposes
// PDF/PNG/JPG/JPEG as requested.)
export const ACCEPTED_MIME_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
];

export const ACCEPTED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg"];
