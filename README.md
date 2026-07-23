# Document Processing Application

A full-stack app for uploading a document, running it through a chosen OCR
engine, and viewing/downloading the extracted content in a chosen output
format — with the original document and the processed output shown
side-by-side.

- **Core features:** File Uploading, OCR Engine Selection, Output Format
  Selection, Extract Action
- **OCR engines:** Tesseract OCR, EasyOCR, PaddleOCR, Docling
- **Output formats:** Markdown, HTML, JSON

---

## Project structure

```
document-processing-app/
├── backend/                        # FastAPI backend (fully implemented)
│   ├── app/
│   │   ├── main.py                 # App entrypoint, CORS, exception handlers, routers
│   │   ├── config.py                # Centralised environment-driven settings
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic request/response models + enums
│   │   ├── routers/
│   │   │   ├── upload.py            # POST /api/upload, GET /api/upload/file/{id}
│   │   │   └── extract.py           # POST /api/extract, GET /api/extract/download/{file}
│   │   ├── services/
│   │   │   ├── ocr_service.py       # Engine factory/dispatcher
│   │   │   ├── formatter_service.py # OCRDocument -> Markdown / HTML / JSON
│   │   │   └── engines/
│   │   │       ├── base.py               # BaseOCREngine interface + OCRDocument/OCRPage
│   │   │       ├── image_loader.py       # PDF/image -> PIL Image pages helper
│   │   │       ├── tesseract_engine.py
│   │   │       ├── easyocr_engine.py
│   │   │       ├── paddleocr_engine.py
│   │   │       └── docling_engine.py
│   │   ├── utils/
│   │   │   └── file_utils.py        # Upload validation, saving, id resolution
│   │   └── core/
│   │       └── exceptions.py        # Custom exception hierarchy -> clean JSON errors
│   ├── storage/
│   │   ├── uploads/                 # Original uploaded files land here
│   │   └── outputs/                 # Generated Markdown/HTML/JSON outputs land here
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/                        # React (Vite) frontend scaffold
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload/          # Drag-and-drop uploader, engine/format selectors
│   │   │   ├── ResultsViewer/       # Side-by-side original vs. processed output view
│   │   │   └── common/              # Buttons, spinners, layout shared components
│   │   ├── pages/
│   │   │   ├── Landing/             # Upload page (Core features live here)
│   │   │   └── Results/             # Results page (original doc + output side-by-side)
│   │   ├── services/
│   │   │   └── api.js                # Axios client wrapping /upload and /extract
│   │   ├── hooks/                    # e.g. useUpload, useExtract (custom hooks)
│   │   ├── context/                  # e.g. DocumentContext for cross-page state
│   │   ├── styles/                   # Global styles / theme
│   │   └── utils/                    # Frontend-only helpers (formatters, validators)
│   ├── public/
│   ├── package.json
│   └── .env.example
│
└── README.md
```

> **Note on scope:** the task asked specifically for the *complete backend
> code*, so the `backend/` folder is a fully working FastAPI service. The
> `frontend/` folder is scaffolded with the recommended structure, a
> package.json, and a ready-to-use API client (`services/api.js`) that
> already matches the backend's request/response shapes — the page and
> component files are stubbed out as empty, clearly named folders ready
> for the actual React components to be filled in.

---

## Backend — how it works

### Request flow

1. **`POST /api/upload`** — the frontend sends the raw file
   (`multipart/form-data`). The backend validates the extension/mime-type
   and size, saves it under `storage/uploads/{file_id}.{ext}`, and returns
   a `file_id` plus a `file_url` the results page can use to render the
   original document.
2. **`POST /api/extract`** — the frontend sends
   `{ file_id, ocr_engine, output_format }`. The backend:
   - resolves the stored file from `file_id`
   - runs the selected OCR engine (`services/ocr_service.py` dispatches to
     the right class in `services/engines/`)
   - normalises the result into an `OCRDocument` (list of `OCRPage`, each
     with `text`, optional `confidence`, and optional layout `elements`)
   - formats that into Markdown / HTML / JSON via `formatter_service.py`
   - saves the formatted output under `storage/outputs/{result_id}.{ext}`
   - returns the formatted text plus a `download_url`
3. **`GET /api/upload/file/{file_id}`** and
   **`GET /api/extract/download/{output_filename}`** stream the original
   file and the generated output file respectively, for the results page's
   side-by-side view and download button.

### Why the engines share one interface

Every OCR engine implements `BaseOCREngine.extract(file_path) -> OCRDocument`
(`services/engines/base.py`). This means:

- Adding a 5th OCR engine later only requires one new file + one line in
  the `_ENGINE_REGISTRY` dict in `ocr_service.py` — nothing else changes.
- The formatter never needs to know which engine produced the text; it
  only looks at the normalised `OCRPage` structure, using the richer
  `elements` list (headings/paragraphs/tables) when an engine like Docling
  provides it, and falling back to plain text otherwise.

### Setup (local development)

```bash
cd backend

# System dependencies (Debian/Ubuntu example):
sudo apt-get install tesseract-ocr poppler-utils

python -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows

pip install -r requirements.txt
cp .env.example .env               # adjust values as needed

uvicorn app.main:app --reload --port 8000
```

The interactive APilable at `http://localhost:8000/docs`.

### Setup (Docker)

```bash
cd backend
docker build -t document-processing-backend .
docker run -p 8000:8000 -v $(pwd)/storage:/app/storage document-processing-backend
```

### Setup (frontend scaffold)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## API summary

| Method | Path                                  | Purpose                                   |
|--------|----------------------------------------|--------------------------------------------|
| POST   | `/api/upload`                          | Upload a PDF/image, get back a `file_id`   |
| GET    | `/api/upload/file/{file_id}`           | Stream the original file                   |
| POST   | `/api/extract`                         | Run OCR + formatting on a `file_id`        |
| GET    | `/api/extract/download/{output_file}`  | Download the generated output file         |
| GET    | `/health`                              | Liveness check                             |

Full request/response schemas are enforced by Pydantic (`app/models/schemas.py`)
and are viewable live in the auto-generated `/docs` page.
