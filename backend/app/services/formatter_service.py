"""
Formatter service.

Converts a normalised `OCRDocument` (produced by any OCR engine) into the
user's requested output format: Markdown, HTML, or JSON.

Engines that provide layout-aware `elements` (currently only Docling)
yield richer Markdown/HTML with real headings, lists, and tables. Plain
text-only engines (Tesseract, EasyOCR, PaddleOCR) fall back to simple
paragraph-per-line rendering.
"""

from __future__ import annotations

import html
import json

import markdown2

from app.core.exceptions import OutputFormatNotSupportedError
from app.models.schemas import OutputFormatType
from app.services.engines.base import OCRDocument

_HTML_DOCUMENT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Extracted Document</title>
</head>
<body>
{body}
</body>
</html>
"""


def format_document(document: OCRDocument, output_format: OutputFormatType) -> str:
    if output_format == OutputFormatType.MARKDOWN:
        return _to_markdown(document)
    if output_format == OutputFormatType.HTML:
        return _to_html(document)
    if output_format == OutputFormatType.JSON:
        return _to_json(document)
    raise OutputFormatNotSupportedError(output_format)


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------

def _to_markdown(document: OCRDocument) -> str:
    sections: list[str] = []
    for page in document.pages:
        sections.append(f"<!-- Page {page.page_number} -->")

        if page.elements:
            sections.append(_elements_to_markdown(page.elements))
        else:
            sections.append(page.text)

    return "\n\n".join(section for section in sections if section.strip())


def _elements_to_markdown(elements: list[dict]) -> str:
    lines: list[str] = []
    for element in elements:
        el_type, text = element["type"], element["text"]
        if el_type == "heading":
            lines.append(f"## {text}")
        elif el_type == "list_item":
            lines.append(f"- {text}")
        elif el_type == "table":
            # Docling tables already arrive as markdown-ish text in this
            # simplified pipeline; wrap in a code fence if it isn't
            # already pipe-delimited so it renders predictably.
            lines.append(text if "|" in text else f"```\n{text}\n```")
        elif el_type == "caption":
            lines.append(f"*{text}*")
        else:  # paragraph, footnote, default
            lines.append(text)
    return "\n\n".join(lines)


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

def _to_html(document: OCRDocument) -> str:
    body_parts: list[str] = []
    for page in document.pages:
        body_parts.append(f'<section class="page" data-page="{page.page_number}">')

        if page.elements:
            body_parts.append(_elements_to_html(page.elements))
        else:
            # markdown2 gives us safe paragraph/line-break handling for
            # plain OCR text without us hand-rolling an HTML escaper.
            body_parts.append(markdown2.markdown(page.text))

        body_parts.append("</section>")

    return _HTML_DOCUMENT_TEMPLATE.format(body="\n".join(body_parts))


def _elements_to_html(elements: list[dict]) -> str:
    html_lines: list[str] = []
    for element in elements:
        el_type, text = element["type"], html.escape(element["text"])
        if el_type == "heading":
            html_lines.append(f"<h2>{text}</h2>")
        elif el_type == "list_item":
            html_lines.append(f"<li>{text}</li>")
        elif el_type == "table":
            html_lines.append(f"<pre class='table-block'>{text}</pre>")
        elif el_type == "caption":
            html_lines.append(f"<figcaption>{text}</figcaption>")
        else:
            html_lines.append(f"<p>{text}</p>")
    return "\n".join(html_lines)


# --------------------------------------------------------------------------
# JSON
# --------------------------------------------------------------------------

def _to_json(document: OCRDocument) -> str:
    payload = {
        "engine": document.engine_name,
        "page_count": len(document.pages),
        "pages": [
            {
                "page_number": page.page_number,
                "text": page.text,
                "confidence": page.confidence,
                "elements": page.elements,
            }
            for page in document.pages
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
