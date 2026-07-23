# --- Backend Dockerfile ---
FROM python:3.11-slim

# System dependencies required by the OCR engines:
#   - tesseract-ocr: Tesseract binary + English language pack
#   - poppler-utils: needed by pdf2image to rasterize PDF pages
#   - libgl1 / libglib2.0-0: required by OpenCV (a dependency of EasyOCR/PaddleOCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p storage/uploads storage/outputs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
