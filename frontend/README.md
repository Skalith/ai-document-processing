# DocExtract — Frontend

React + Vite frontend for the existing FastAPI OCR backend. This package
contains **frontend code only** — no backend files were modified, renamed,
or added.

## Setup

```bash
cd frontend
npm install
cp .env.example .env     # adjust VITE_API_BASE_URL if your backend isn't on :8000
npm run dev
```

Make sure the FastAPI backend is running (`uvicorn app.main:app --reload --port 8000`)
and that `CORS_ORIGINS` in the backend's `.env` includes `http://localhost:5173`.

## Pages

- **`/` — Upload Page** (`src/pages/Landing/UploadPage.jsx`)
  Drag-and-drop / click-to-upload box (PDF, PNG, JPG, JPEG), OCR engine
  select, output format select, and an Extract button.
- **`/result` — Result Page** (`src/pages/Results/ResultPage.jsx`)
  Split-screen: original document on the left (PDF viewer or image
  preview), OCR output on the right, rendered according to the chosen
  output format.

## Exact API mapping (no invented endpoints)

| Action | Method | Path | Backend source |
|---|---|---|---|
| Upload file | `POST` | `{VITE_API_BASE_URL}/upload` (multipart, field `file`) | `app/routers/upload.py::upload_file` |
| Serve original file | `GET` | `{VITE_API_BASE_URL}/upload/file/{file_id}` | `app/routers/upload.py::get_original_file` |
| Run extraction | `POST` | `{VITE_API_BASE_URL}/extract` (`{ file_id, ocr_engine, output_format }`) | `app/routers/extract.py::extract_document` |
| Download formatted output | `GET` | `{VITE_API_BASE_URL}/extract/download/{output_filename}` | `app/routers/extract.py::download_output` |

`ocr_engine` values: `tesseract`, `easyocr`, `paddleocr`, `docling`
`output_format` values: `markdown`, `html`, `json`

These match `OCREngineType` / `OutputFormatType` in
`backend/app/models/schemas.py` exactly — see `src/utils/constants.js`.

All request/response handling lives in `src/services/api.js`, which is a
thin Axios wrapper with no business logic of its own.

## One added dependency: `react-markdown`

The stack requested was React + Vite + Router + Axios + MUI. I added
**`react-markdown`** (rendering only, no network calls, no schema
assumptions) so that Markdown output can be shown rendered rather than
as raw text. Every format also has a **Preview / Raw** toggle (Markdown
and HTML) so you can always see byte-for-byte what the backend returned.
JSON is shown as the pretty-printed string the backend already produces
— it isn't re-parsed or reformatted client-side.

## Notes

- The Result page persists the last upload/extraction response in
  `sessionStorage` (`src/context/ExtractionContext.jsx`) purely so a
  browser refresh on `/result` doesn't blank the page — no backend
  history/database logic is involved.
- HTML output is rendered inside a sandboxed `<iframe srcDoc>` since the
  backend returns a full HTML document (`<!DOCTYPE html>…`), which
  wouldn't parse correctly if injected into a `<div>`.
- PDF preview uses the browser's native PDF viewer via `<iframe src=...>`
  pointing straight at the backend's file-serving endpoint — no extra PDF
  library needed.
