# DocExtract — Intelligent AI Document Processing Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Material UI](https://img.shields.io/badge/UI-Material%20UI%20v5-007FFF?style=flat-square&logo=mui)](https://mui.com/)
[![Pydantic v2](https://img.shields.io/badge/Validation-Pydantic%20v2-E92063?style=flat-square&logo=pydantic)](https://docs.pydantic.dev/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![Langfuse](https://img.shields.io/badge/Observability-Langfuse-000000?style=flat-square)](https://langfuse.com/)

**DocExtract** is a full-stack, enterprise-grade AI document processing platform designed to ingest complex multi-page documents (PDFs, scans, invoices, receipts, resumes, and forms), intelligently extract and classify content using **hybrid OCR** and **LLM structured reasoning**, validate data against strict Pydantic schemas, and provide a side-by-side **human-in-the-loop verification and editing suite** with customizable UI themes.

---

## Table of Contents

- [Key Features](#key-features)
- [Architecture & Data Flow](#architecture--data-flow)
- [Project Directory Structure](#project-directory-structure)
- [Core Components](#core-components)
  - [1. Hybrid OCR & Document Ingestion](#1-hybrid-ocr--document-ingestion)
  - [2. Multi-Provider LLM Chain with Failover](#2-multi-provider-llm-chain-with-failover)
  - [3. Dynamic Schema Selection & Validation](#3-dynamic-schema-selection--validation)
  - [4. Asynchronous Job Queue & Cancellation](#4-asynchronous-job-queue--cancellation)
  - [5. Side-by-Side Results & Human Verification Layer](#5-side-by-side-results--human-verification-layer)
  - [6. Theming System (7 Selectable Themes)](#6-theming-system-7-selectable-themes)
- [API Reference](#api-reference)
  - [Endpoints Summary](#endpoints-summary)
  - [Request & Response Payloads](#request--response-payloads)
- [Environment Configuration](#environment-configuration)
- [Installation & Getting Started](#installation--getting-started)
  - [Prerequisites & System Libraries](#prerequisites--system-libraries)
  - [Quick Start (One-Command Launcher)](#quick-start-one-command-launcher)
  - [Manual Setup (Step-by-Step)](#manual-setup-step-by-step)
  - [Docker Setup](#docker-setup)
- [Tech Stack Details](#tech-stack-details)
- [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Key Features

- ⚡ **Hybrid OCR Pipeline**: Intelligently inspects multi-page PDFs using PyMuPDF (`fitz`). High-speed native digital text extraction is applied to machine-readable pages, while scanned/raster pages are routed page-by-page through selected OCR engines.
- 🔍 **4 Modular OCR Engines**: Built on an interchangeable factory pattern:
  - **Tesseract OCR**: Robust, battle-tested open-source OCR.
  - **EasyOCR**: Deep-learning OCR with 80+ language support.
  - **PaddleOCR**: Ultra-fast and accurate text detection/recognition.
  - **IBM Docling**: Advanced document layout analysis, reading-order reconstruction, and native table structure parsing.
- 🤖 **Multi-Provider LLM Fallback Chain**: Zero-downtime structured intelligence. Ingested documents are routed through an automated provider failover chain:
  `OmniRoute -> Gemini (Google) -> Groq -> NVIDIA NIM -> Anthropic (Claude)`
  If an API key is missing or fails due to rate limits, the pipeline automatically falls over to the next provider. If all LLMs fail, it fails soft to raw OCR text formatting without crashing.
- 🔭 **Full Observability with Langfuse**: Built-in non-blocking instrumentation traces model names, latency, prompts, token counts, and costs across every classification and extraction phase.
- 📋 **Dynamic Classification & Typed Schemas**: Automatically classifies documents as `invoice`, `receipt`, `resume`, or `other`, selecting dedicated Pydantic schemas for guaranteed structured JSON output.
- ⏳ **Async Job Engine with Live Progress & Cancellation**: Background `asyncio.Task` pipeline returning HTTP `202 Accepted`. The UI shows a real-time progress overlay (0–100%) broken down by granular stages (Resolving -> Page Analysis -> Per-Page OCR -> Classification -> Structured Extraction -> Formatting) with a cooperative **"Stop Extraction"** cancel button.
- ✍️ **Human-in-the-Loop Verification & Edit Layer**:
  - Implements a dual-state architecture: original immutable `ai_result` alongside user-corrected `user_result`.
  - Recursive, type-aware structured editor (`FieldEditor.jsx`) supporting dotted-path changes (e.g. `line_items[0].amount`).
  - Real-time diff tracking and audit log (`changes[]`), one-click **"Reset to AI Result"**, and browser session persistence.
- 📑 **Synchronized Side-by-Side Viewer**: Left-hand pane embeds the original PDF (via browser native PDF viewer with `inline` disposition) or high-res image; right-hand pane renders extracted output with **Preview vs. Raw** toggles for Markdown and HTML, or pretty-printed JSON.
- 🎨 **7 Handcrafted UI Themes**: Switch themes on the fly from the navigation bar (Obsidian Dark, Clean Light, Midnight Aurora, Glassmorphism, Ocean Blue, Emerald, Sunset) with persistent local storage.

---

## Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Client ["Frontend (React 18 + Vite + MUI)"]
        UI_Upload["Upload Page (Dropzone, Engine & Format Select)"]
        UI_Progress["Progress Overlay (Polling + Cancel Action)"]
        UI_Viewer["Side-by-Side Viewer (Original vs Extracted)"]
        UI_Editor["Human Verification Editor (Dotted-Path Diff & Audit)"]
    end

    subgraph API ["FastAPI Backend (:8000)"]
        Router_Upload["/api/upload"]
        Router_Extract["/api/extract"]
        Router_Jobs["/api/extract/jobs/{id}"]
        Router_Cancel["/api/extract/jobs/{id}/cancel"]
        Job_Manager["In-Memory JobManager (Asyncio Tasks)"]
    end

    subgraph Ingestion ["Hybrid Document Ingestion"]
        PyMuPDF["PyMuPDF (fitz) Page Classifier"]
        NativeText["Native Text Extractor"]
        Pdf2Image["pdf2image (Page Rasterizer)"]
    end

    subgraph OCREngines ["OCR Service Engine Registry"]
        Tesseract["Tesseract OCR"]
        EasyOCR["EasyOCR"]
        PaddleOCR["PaddleOCR"]
        Docling["IBM Docling (Layout & Tables)"]
    end

    subgraph LLMChain ["Multi-Provider LLM Chain (with Langfuse Tracing)"]
        direction TB
        P_Omni["OmniRoute Gateway"]
        P_Gemini["Google Gemini"]
        P_Groq["Groq (Llama / Mistral)"]
        P_Nvidia["NVIDIA NIM"]
        P_Claude["Anthropic Claude"]
        P_Omni -->|failover| P_Gemini -->|failover| P_Groq -->|failover| P_Nvidia -->|failover| P_Claude
    end

    subgraph OutputFormatting ["Output & Persistence"]
        Formatter["Structured / Text Formatter (Markdown / HTML / JSON)"]
        DiskStorage[("Storage (/storage/uploads & /storage/outputs)")]
    end

    UI_Upload -->|POST multipart/form-data| Router_Upload
    Router_Upload --> DiskStorage
    UI_Upload -->|POST ExtractRequest| Router_Extract
    Router_Extract -->|Spawn async task| Job_Manager
    Job_Manager --> PyMuPDF

    PyMuPDF -->|Machine-Readable Pages| NativeText
    PyMuPDF -->|Scanned / Image Pages| Pdf2Image
    Pdf2Image --> OCREngines

    NativeText --> Assembly["Assemble Document Pages"]
    OCREngines --> Assembly

    Assembly --> LLMChain
    LLMChain -->|1. Classify Document Type| DocType["Type: invoice, receipt, resume, other"]
    DocType -->|2. Dynamic Schema Selection| PydanticValidation["Pydantic Schema Validation"]
    PydanticValidation --> Formatter

    Formatter --> DiskStorage
    UI_Progress <-->|Poll GET /jobs/{id}| Router_Jobs
    UI_Progress -->|POST cancel| Router_Cancel
    Router_Jobs --> Job_Manager

    DiskStorage --> UI_Viewer
    UI_Viewer <--> UI_Editor
```

---

## Project Directory Structure

```
ai-document-processing/
├── start.sh                       # One-command startup script (boots backend + frontend, handles logs & process groups)
├── working.md                     # Development work log & change history
├── weakness.md                    # Engineering analysis, edge cases, and feature specifications
├── logs/                          # Runtime log directory (backend.log, frontend.log)
│
├── backend/                       # FastAPI Backend Service
│   ├── Dockerfile                 # Container definition with system poppler/tesseract dependencies
│   ├── requirements.txt           # Python dependencies (pinned versions)
│   ├── .env.example               # Template environment configuration
│   ├── storage/
│   │   ├── uploads/               # Uploaded source files (UUID-named)
│   │   └── outputs/               # Formatted output artifacts (.md, .html, .json)
│   └── app/
│       ├── main.py                # FastAPI entrypoint, CORS setup, global exception handlers
│       ├── config.py              # Pydantic BaseSettings loading from .env
│       ├── core/
│       │   └── exceptions.py      # Custom exception hierarchy (AppException, LLMServiceError, etc.)
│       ├── models/
│       │   └── schemas.py         # Request/Response models, Enums (OCREngineType, DocumentType, JobStatus)
│       ├── routers/
│       │   ├── upload.py          # POST /api/upload, GET /api/upload/file/{id} (inline file streaming)
│       │   └── extract.py         # POST /api/extract (async job), GET /jobs/{id}, POST /jobs/{id}/cancel
│       ├── prompts/               # System and user prompts for LLM document processing
│       │   ├── classifier.py      # Prompt for document classification
│       │   ├── invoice_prompt.py  # Prompt for invoice field extraction
│       │   ├── receipt_prompt.py  # Prompt for receipt field extraction
│       │   ├── resume_prompt.py   # Prompt for resume parsing
│       │   └── generic_prompt.py  # Fallback prompt for arbitrary documents
│       ├── schemas/               # Structured Pydantic validation schemas
│       │   ├── invoice.py         # InvoiceSchema (line items, tax, vendor, totals)
│       │   ├── receipt.py         # ReceiptSchema (merchant, totals, items, payment)
│       │   ├── resume.py          # ResumeSchema (work experience, education, skills)
│       │   └── generic.py         # GenericDocumentSchema (key-value entities)
│       ├── services/
│       │   ├── jobs.py            # ExtractionJob & JobManager for asynchronous task lifecycle
│       │   ├── ocr_service.py     # OCR engine dispatcher & registry
│       │   ├── formatter_service.py # Plain OCR document to Markdown, HTML, or JSON
│       │   ├── layout_service.py  # LayoutParser & Detectron2 reading-order reconstruction
│       │   ├── engines/           # Concrete OCR implementations
│       │   │   ├── base.py        # BaseOCREngine abstract interface & OCRDocument / OCRPage models
│       │   │   ├── image_loader.py# PDF to PIL Image conversion utilities
│       │   │   ├── tesseract_engine.py
│       │   │   ├── easyocr_engine.py
│       │   │   ├── paddleocr_engine.py
│       │   │   └── docling_engine.py
│       │   ├── pdf/               # Hybrid extraction utilities
│       │   │   ├── page_detector.py # PyMuPDF page classification (native vs scanned)
│       │   │   └── hybrid_extraction_service.py # Per-page hybrid execution with progress reporting
│       │   └── llm/               # LLM intelligence layer
│       │       ├── llm_client.py  # Public facade `call_llm_for_json` with Langfuse tracing
│       │       ├── classifier_service.py # Document classification execution
│       │       ├── extraction_service.py # Schema-driven structured field extraction
│       │       ├── schema_selector.py    # Schema router mapping document types to Pydantic models
│       │       ├── structured_output_formatter.py # Formats structured dicts into Markdown, HTML, JSON
│       │       └── providers/     # Multi-provider implementations
│       │           ├── base.py    # Base LLMProvider & LLMResult classes
│       │           ├── factory.py # Provider chain builder (ordered priority)
│       │           ├── openai_compat.py # Shared client for OpenAI-compatible APIs
│       │           ├── omniroute_provider.py
│       │           ├── gemini_provider.py
│       │           ├── groq_provider.py
│       │           ├── nvidia_provider.py
│       │           └── anthropic_provider.py
│       └── utils/
│           └── file_utils.py      # Secure file storage, UUID naming, mime-type validation
│
└── frontend/                      # React 18 + Vite Frontend Application
    ├── package.json               # Node dependencies (MUI v5, react-markdown, axios, react-router-dom)
    ├── vite.config.js             # Vite configuration
    ├── index.html                 # HTML entry with typography fonts
    ├── .env.example               # Frontend environment template (VITE_API_BASE_URL)
    └── src/
        ├── main.jsx               # React DOM root render
        ├── App.jsx                # Theme & Context providers, client routing
        ├── theme.js               # 7 MUI theme configurations with design tokens
        ├── context/
        │   ├── ExtractionContext.jsx # Session storage for upload and extraction results
        │   ├── ThemeContext.jsx      # Theme preference provider persisted to localStorage
        │   └── UserResultContext.jsx # State store for human verification edits and change history
        ├── services/
        │   └── api.js             # Axios client wrapping backend API endpoints
        ├── utils/
        │   ├── constants.js       # OCR engine enums, MIME types, format labels
        │   └── formatBytes.js     # Human-readable file size formatter
        ├── pages/
        │   ├── Landing/
        │   │   └── UploadPage.jsx # Document upload dropzone, engine/format controls, extraction kickoff
        │   └── Results/
        │       └── ResultPage.jsx # Dual-pane viewer, edit-mode toggles, action bar
        └── components/
            ├── FileUpload/
            │   └── FileUploadBox.jsx # Drag-and-drop file target with file type validation
            ├── Progress/
            │   └── ProcessingProgress.jsx # Full-screen modal with progress bar, stage text & cancel button
            ├── ResultsViewer/
            │   ├── OriginalDocumentViewer.jsx # Native inline PDF iframe / image viewer
            │   └── ExtractedOutputViewer.jsx  # Rendered Markdown / HTML iframe / JSON view & Edit trigger
            ├── ResultEditor/      # Human-in-the-Loop verification module
            │   ├── VerifyModeBar.jsx   # Top editing toolbar with change count, Save, and Cancel
            │   ├── FieldEditor.jsx     # Recursive, type-aware nested field editor with change badges
            │   └── changeTracker.js    # Immutable diff algorithm and dotted-path leaf tracking
            ├── Theme/
            │   └── ThemeButton.jsx     # Dropdown menu button for switching the 7 themes
            └── common/
                └── ErrorAlert.jsx      # Standardized dismissible error callout
```

---

## Core Components

### 1. Hybrid OCR & Document Ingestion

Rather than treating every document as a flat set of scanned pixels, DocExtract uses a two-tier hybrid ingestion strategy:

1. **Page Classification (`page_detector.py`)**: Uses PyMuPDF (`fitz`) to count non-whitespace native text characters on each page.
   - If characters >= `MIN_NATIVE_TEXT_CHARS` (default: 20), the page is marked as **machine-readable**. Native digital text is extracted directly in milliseconds without running OCR.
   - If characters < `MIN_NATIVE_TEXT_CHARS`, the page is marked as **scanned**.
2. **Granular OCR Processing (`hybrid_extraction_service.py`)**: Only the scanned pages are converted to images (using `pdf2image` at 200 DPI) and dispatched to the user's chosen OCR engine. This avoids unnecessary rasterization, preserves 100% digital text fidelity, and dramatically speeds up processing.

#### Available OCR Engines
| Engine | Best Used For | Layout / Table Support | Performance |
|---|---|---|---|
| **Tesseract** | Standard printed documents, forms, books | Bounding box words/blocks | Fast (CPU) |
| **EasyOCR** | Natural scenes, mixed-orientation scans, multi-lingual docs | Line-level confidence | Moderate (CPU/GPU) |
| **PaddleOCR** | High-density tables, multi-lingual receipts | Line/Word detection | Fast (CPU/GPU) |
| **Docling** | Complex PDFs, multi-column articles, financial tables | Full native tables, reading order | Deep parsing |

### 2. Multi-Provider LLM Chain with Failover

The platform features an automated, resilient LLM dispatch layer in `backend/app/services/llm/llm_client.py`. Each provider is evaluated sequentially:

`OmniRoute -> Gemini -> Groq -> NVIDIA NIM -> Anthropic`

- **Failover Mechanism**: If a provider is missing its API key, returns a 429 rate limit, or fails to return valid JSON, the request immediately falls over to the next provider in line.
- **Fail-Soft Safety**: If no API keys are provided or all providers fail, the system automatically falls back to raw OCR text output. The user still receives their document extraction without server crashes.
- **Langfuse Telemetry**: Wraps every call in an `@observe` span with nested provider generations, capturing exact token counts, latency, and system prompts.

### 3. Dynamic Schema Selection & Validation

Once text is extracted, it undergoes structured intelligence processing:
1. **Classification**: `classifier_service.py` identifies whether the document is an `invoice`, `receipt`, `resume`, or `other`.
2. **Schema Binding**: `schema_selector.py` binds the detected document type to its corresponding Pydantic schema (`InvoiceSchema`, `ReceiptSchema`, etc.).
3. **Structured Extraction**: The chosen LLM extracts typed fields (e.g. invoice dates, line items, monetary totals, line quantities, merchant info).
4. **Validation**: The JSON output is parsed through the Pydantic model. If validation succeeds, `structured_output_formatter.py` produces cleanly structured Markdown, HTML, or JSON.

### 4. Asynchronous Job Queue & Cancellation

Extraction of large documents can take time. To ensure a responsive user experience:
- `POST /api/extract` immediately enqueues the request as a background `asyncio.Task` and returns an HTTP `202 Accepted` response with an `ExtractJobResponse`.
- The frontend progress dialog (`ProcessingProgress.jsx`) polls `GET /api/extract/jobs/{job_id}` every 800ms, displaying:
  - Total progress percentage (0–100%)
  - Human-readable stage descriptions (*"Classifying document (LLM)…"*, *"OCR scanning page 2 (1/3)…"*)
- Users can click **Stop Extraction** at any moment (`POST /api/extract/jobs/{job_id}/cancel`). The backend checks an `asyncio.Event` before every stage and between every scanned page to terminate execution immediately and free server resources.

### 5. Side-by-Side Results & Human Verification Layer

The Results page (`ResultPage.jsx`) provides a split-screen view:
- **Left Pane**: Displays the original document. PDFs are streamed with `content_disposition_type="inline"`, enabling native in-browser PDF panning, zooming, and page navigation inside an iframe.
- **Right Pane**: Displays the extracted text with a **Preview vs. Raw** switch for Markdown and HTML, or pretty-printed JSON.

#### Human-in-the-Loop Verification / Edit Workflow
1. When structured extraction succeeds, an **"✏️ Edit Result"** button appears.
2. Clicking it opens `VerifyModeBar.jsx` and the recursive `FieldEditor.jsx`.
3. Users can directly modify scalar fields (e.g. adjust an incorrect total, change a date) or edit nested array elements (e.g. line items).
4. As fields are modified:
   - Modified fields display an `"Edited"` indicator badge.
   - The top toolbar displays a real-time count of modified fields.
5. Clicking **Save Changes** creates a `user_result` with an immutable diff record (`changes[]`), saving it to `localStorage`.
6. Users can click **Reset to AI Result** at any time to discard modifications and restore the original AI extraction.

### 6. Theming System (7 Selectable Themes)

DocExtract includes 7 built-in themes configured via Material-UI design tokens in `frontend/src/theme.js`. Preferences are saved to `localStorage` and apply instantly across all pages:

| Theme | Icon | Palette Characteristics |
|---|:---:|---|
| **Clean Light** *(Default)* | ☀️ | Minimalist crisp off-white background (`#F5F6F8`) with teal primary accents (`#0F8B8D`). |
| **Obsidian Dark** | 🌑 | Deep charcoal background (`#0B0E13`), dark paper (`#151B23`), and glowing cyan accents. |
| **Midnight Aurora** | 🌌 | Dark navy space palette (`#0A0E1F`) with soft purple and mint aurora accents. |
| **Glassmorphism** | 💎 | Vivid 3-stop gradient background with translucent frosted-glass panels (`backdrop-filter: blur(14px)`). |
| **Ocean Blue** | 🌊 | Clean corporate ice-blue palette (`#EEF4FB`) with deep sapphire accents. |
| **Emerald** | 🌿 | Soft botanical green palette (`#F1F7F2`) with deep forest accents. |
| **Sunset** | 🌅 | Warm desert sand background (`#FFF4EC`) with terracotta and coral accents. |

---

## API Reference

The interactive OpenAPI documentation is available at `http://localhost:8000/docs` when running the backend.

### Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Uploads a PDF or image; validates MIME type and file size; returns `file_id`. |
| `GET` | `/api/upload/file/{file_id}` | Streams the original uploaded file with `inline` disposition for browser viewing. |
| `POST` | `/api/extract` | Enqueues an async extraction task; returns HTTP 202 with `job_id`. |
| `GET` | `/api/extract/jobs/{job_id}` | Polls the current job status, progress percentage, stage, and final result. |
| `POST` | `/api/extract/jobs/{job_id}/cancel` | Cooperatively cancels an in-flight extraction job. |
| `GET` | `/api/extract/download/{output_file}` | Downloads the generated Markdown, HTML, or JSON file. |
| `GET` | `/health` | Liveness check returning API status and service name. |

---

### Request & Response Payloads

#### 1. Upload File
`POST /api/upload` (multipart/form-data)

**Form Data**: `file: <Binary>` (PDF, PNG, JPG, JPEG, TIFF, BMP, up to 25 MB)

**Response (200 OK)**:
```json
{
  "file_id": "7775337b045c4663af39db0a5ca1e5d6",
  "original_filename": "invoice_sample.pdf",
  "stored_filename": "7775337b045c4663af39db0a5ca1e5d6.pdf",
  "content_type": "application/pdf",
  "size_bytes": 104230,
  "page_count": 2,
  "file_url": "/api/upload/file/7775337b045c4663af39db0a5ca1e5d6",
  "uploaded_at": "2026-09-09T11:30:00Z"
}
```

#### 2. Start Extraction Job
`POST /api/extract` (application/json)

**Request Body**:
```json
{
  "file_id": "7775337b045c4663af39db0a5ca1e5d6",
  "ocr_engine": "tesseract",
  "output_format": "markdown"
}
```
*Allowed `ocr_engine` values: `tesseract`, `easyocr`, `paddleocr`, `docling`*  
*Allowed `output_format` values: `markdown`, `html`, `json`*

**Response (202 Accepted)**:
```json
{
  "job_id": "c6204c3d8bb247bc865d1d64c1bb2542",
  "file_id": "7775337b045c4663af39db0a5ca1e5d6",
  "status": "queued",
  "progress": 0,
  "stage": "Job created",
  "created_at": "2026-09-09T11:30:01Z",
  "error": null,
  "result": null
}
```

#### 3. Poll Extraction Job Status
`GET /api/extract/jobs/{job_id}`

**Response (In Progress - 200 OK)**:
```json
{
  "job_id": "c6204c3d8bb247bc865d1d64c1bb2542",
  "file_id": "7775337b045c4663af39db0a5ca1e5d6",
  "status": "processing",
  "progress": 75,
  "stage": "Classifying document (LLM)…",
  "created_at": "2026-09-09T11:30:01Z",
  "error": null,
  "result": null
}
```

**Response (Completed - 200 OK)**:
```json
{
  "job_id": "c6204c3d8bb247bc865d1d64c1bb2542",
  "file_id": "7775337b045c4663af39db0a5ca1e5d6",
  "status": "completed",
  "progress": 100,
  "stage": "Completed",
  "created_at": "2026-09-09T11:30:01Z",
  "error": null,
  "result": {
    "result_id": "377033fbadfd4670bb1391304267c514",
    "file_id": "7775337b045c4663af39db0a5ca1e5d6",
    "ocr_engine": "tesseract",
    "output_format": "markdown",
    "status": "completed",
    "pages": [
      { "page_number": 1, "text": "INVOICE #INV-1024...", "confidence": 94.2 }
    ],
    "formatted_output": "## Invoice\n- **Invoice Number:** INV-1024\n...",
    "download_url": "/api/extract/download/377033fbadfd4670bb1391304267c514.md",
    "processing_time_seconds": 2.45,
    "created_at": "2026-09-09T11:30:04Z",
    "document_type": "invoice",
    "structured_data": {
      "invoice_number": "INV-1024",
      "vendor_name": "Acme Supplies Ltd",
      "invoice_date": "2026-08-15",
      "total_amount": 1450.00,
      "tax_amount": 145.00,
      "line_items": [
        { "description": "Cloud Servers", "quantity": 2, "unit_price": 650.00, "total": 1300.00 }
      ]
    },
    "used_structured_extraction": true
  }
}
```

#### 4. Cancel Running Job
`POST /api/extract/jobs/{job_id}/cancel`

**Response (200 OK)**:
```json
{
  "job_id": "c6204c3d8bb247bc865d1d64c1bb2542",
  "status": "cancelled",
  "progress": 75,
  "stage": "Cancelled",
  "error": null,
  "result": null
}
```

---

## Environment Configuration

### Backend Configuration (`backend/.env`)

Copy `backend/.env.example` to `backend/.env` and supply your keys. All keys are optional — missing keys gracefully skip the corresponding provider or feature.

```env
# Application Settings
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
UPLOAD_DIR=storage/uploads
OUTPUT_DIR=storage/outputs
MAX_UPLOAD_SIZE_MB=25
MIN_NATIVE_TEXT_CHARS=20

# Multi-Provider LLM Keys (Priority: OmniRoute -> Gemini -> Groq -> NVIDIA -> Anthropic)
# 1. OmniRoute Gateway (OpenAI-compatible)
OMNIROUTE_API_KEY=
OMNIROUTE_MODEL=auto
OMNIROUTE_BASE_URL=http://localhost:20128/v1

# 2. Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash

# 3. Groq (OpenAI-compatible)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

# 4. NVIDIA NIM
NVIDIA_API_KEY=your_nvidia_nim_key_here
NVIDIA_MODEL=meta/llama-3.3-70b-instruct

# 5. Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5

# LLM Generation Defaults
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.0

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

### Frontend Configuration (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env`:

```env
# FastAPI Backend URL
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## Installation & Getting Started

### Prerequisites & System Libraries

The backend requires system-level libraries for PDF rasterization and Tesseract OCR:

#### Debian / Ubuntu / Linux Mint
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils libmagic1
```

#### macOS (Homebrew)
```bash
brew install tesseract poppler libmagic
```

---

### Quick Start (One-Command Launcher)

A comprehensive launcher script `start.sh` is provided in the project root. It will:
1. Verify / automatically create the Python virtual environment (`backend/venv`).
2. Install / update all required Python packages and Node packages.
3. Launch the FastAPI backend on `http://localhost:8000` (with Uvicorn hot-reload).
4. Launch the React Vite frontend on `http://localhost:5173`.
5. Stream both services' logs live with color-coded tags.
6. Cleanly shut down all child process groups upon pressing `Ctrl+C`.

```bash
chmod +x start.sh
./start.sh
```

---

### Manual Setup (Step-by-Step)

#### Step 1: Run the Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your LLM API keys (optional)

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend API will be live at `http://localhost:8000`, and OpenAPI docs at `http://localhost:8000/docs`.

#### Step 2: Run the Frontend

In a separate terminal:

```bash
cd frontend

# Install Node dependencies
npm install

# Configure environment
cp .env.example .env

# Start Vite development server
npm run dev
```
Frontend web application will be accessible at `http://localhost:5173`.

---

### Docker Setup

To build and containerize the backend service:

```bash
cd backend
docker build -t docextract-backend .
docker run -p 8000:8000 -v $(pwd)/storage:/app/storage docextract-backend
```

---

## Tech Stack Details

### Backend
- **FastAPI (0.115.0)**: Modern asynchronous REST API framework.
- **Uvicorn (0.30.6)**: Lightning-fast ASGI web server.
- **Pydantic v2 (2.13.5)**: Type enforcement, JSON schema validation, and dynamic model generation.
- **PyMuPDF / fitz (1.24.10)**: Fast C-based PDF text layer parsing and extraction.
- **pdf2image (1.17.0)**: Poppler-based PDF-to-image rasterization.
- **PyTesseract (0.3.13) & Tesseract-OCR**: Optical character recognition engine.
- **EasyOCR (1.7.2) & PyTorch (2.4.1)**: Neural network-based text detection and recognition.
- **PaddleOCR (2.8.1) & PaddlePaddle (2.6.2)**: High-performance multi-language OCR.
- **Docling (2.7.0)**: IBM layout analysis and table structure parsing.
- **Google GenAI SDK (2.22.0)** & **OpenAI SDK (3.9.0)** & **Anthropic SDK (0.34.2)**: LLM client interfaces.
- **Langfuse (4.15.1)**: Distributed LLM tracing and analytics.
- **Aiofiles (24.1.0)**: Asynchronous non-blocking file system I/O.
- **Loguru (0.7.2)**: Structured logging.

### Frontend
- **React (18.3.1) & Vite (5.4.2)**: Reactive client-side architecture with HMR.
- **Material-UI v5 (@mui/material, @mui/icons-material)**: Component design system.
- **React Router DOM (6.26.0)**: Client routing (`/` and `/result`).
- **Axios (1.7.7)**: HTTP client with upload progress hooks and cancellation support.
- **React-Markdown (9.0.1)**: Safe client-side Markdown rendering.

---

## Troubleshooting & FAQ

#### 1. "pdf2image.exceptions.PDFInfoNotInstalledError: Unable to get page count. Is poppler installed?"
- **Cause**: `poppler-utils` is not installed on your operating system.
- **Fix**: Run `sudo apt-get install -y poppler-utils` (Ubuntu/Debian) or `brew install poppler` (macOS).

#### 2. "tesseract is not installed or it's not in your PATH"
- **Cause**: The Tesseract executable is missing from your system.
- **Fix**: Install Tesseract via `sudo apt-get install -y tesseract-ocr`. If Tesseract is installed in a non-standard directory, specify its absolute path in `backend/.env` using `TESSERACT_CMD=/usr/bin/tesseract`.

#### 3. "What happens if I don't set any LLM API keys?"
- **Answer**: The application is designed to be 100% functional without any LLM keys. The backend detects that no providers are configured and gracefully returns the formatted raw OCR output. The document classification and structured editing features will simply indicate that AI structured extraction is inactive.

#### 4. "How do I cancel a stuck or long-running extraction?"
- **Answer**: During extraction, the progress overlay displays a **"Stop extraction"** button. Clicking this signals the backend job runner to stop at the next page boundary or pipeline checkpoint, terminating the background task and returning the job status as `cancelled`.

---

## License

This project is open-source software licensed under the MIT License.
