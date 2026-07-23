// Thin Axios wrapper around the existing FastAPI backend.
// Every function here maps 1:1 to a real endpoint already defined in
// backend/app/routers/upload.py and backend/app/routers/extract.py.
// No endpoints are invented — payloads/response shapes match
// backend/app/models/schemas.py exactly.

import axios from "axios";

// e.g. "http://localhost:8000/api" (see backend app/config.py -> api_prefix)
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

// Origin only (no /api suffix) — used to resolve the absolute URLs the
// backend hands back (file_url, download_url are already prefixed with /api/...)
const API_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, "");

export const api = axios.create({ baseURL: API_BASE_URL });

/**
 * POST /api/upload  (multipart/form-data, field name: "file")
 * Backend: app.routers.upload.upload_file
 * Returns UploadResponse: { file_id, original_filename, stored_filename,
 *   content_type, size_bytes, page_count, file_url, uploaded_at }
 */
export async function uploadDocument(file, { onUploadProgress } = {}) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return data;
}

/**
 * POST /api/extract  (application/json)
 * Backend: app.routers.extract.extract_document
 * Body shape must match ExtractRequest exactly: { file_id, ocr_engine, output_format }
 * Returns ExtractResponse: { result_id, file_id, ocr_engine, output_format,
 *   status, pages[], formatted_output, download_url, processing_time_seconds, created_at }
 */
export async function extractDocument({ fileId, ocrEngine, outputFormat }) {
  const { data } = await api.post("/extract", {
    file_id: fileId,
    ocr_engine: ocrEngine,
    output_format: outputFormat,
  });
  return data;
}

/**
 * Resolves the absolute URL for the original uploaded file.
 * The backend already returns a relative, prefixed path
 * (e.g. "/api/upload/file/{file_id}") via GET app.routers.upload.get_original_file.
 */
export function resolveFileUrl(relativeUrl) {
  if (!relativeUrl) return null;
  return `${API_ORIGIN}${relativeUrl}`;
}

/**
 * Resolves the absolute URL for a generated output file.
 * Backend endpoint: GET app.routers.extract.download_output
 */
export function resolveDownloadUrl(relativeUrl) {
  if (!relativeUrl) return null;
  return `${API_ORIGIN}${relativeUrl}`;
}

/**
 * Normalizes Axios/backend errors into a plain, displayable message.
 * The backend's global exception handlers (see app/main.py) always
 * return JSON in the shape { detail: string }, so we prefer that.
 */
export function getErrorMessage(error) {
  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error?.message === "Network Error") {
    return "Could not reach the server. Is the backend running?";
  }
  return error?.message || "Something went wrong. Please try again.";
}
