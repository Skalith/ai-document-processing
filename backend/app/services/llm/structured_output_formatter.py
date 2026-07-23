"""
Structured output conversion - Step 8 of the pipeline.

Takes the validated dict produced by extraction_service and the
classified document type, and renders it into the user's requested
output format. This mirrors formatter_service.py's job but operates on
typed structured data instead of a flat OCRDocument, so results pages
get a clean key/value + table view instead of a wall of OCR text once
structured extraction succeeds.
"""

from __future__ import annotations

import html
import json

from app.models.schemas import DocumentType, OutputFormatType

_HTML_DOCUMENT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Structured Extraction - {document_type}</title>
</head>
<body>
{body}
</body>
</html>
"""


def format_structured_output(
    document_type: DocumentType, structured_data: dict, output_format: OutputFormatType
) -> str:
    if output_format == OutputFormatType.JSON:
        return _to_json(document_type, structured_data)
    if output_format == OutputFormatType.MARKDOWN:
        return _to_markdown(document_type, structured_data)
    if output_format == OutputFormatType.HTML:
        return _to_html(document_type, structured_data)
    raise ValueError(f"Unsupported output format: {output_format}")


def _to_json(document_type: DocumentType, data: dict) -> str:
    payload = {"document_type": document_type.value, "data": data}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _to_markdown(document_type: DocumentType, data: dict, _depth: int = 0) -> str:
    lines: list[str] = []
    if _depth == 0:
        lines.append(f"## {document_type.value.title()}")

    for key, value in data.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            if not value:
                continue
            lines.append(f"\n**{label}**")
            for item in value:
                if isinstance(item, dict):
                    row = ", ".join(f"{k}: {v}" for k, v in item.items() if v not in (None, ""))
                    lines.append(f"- {row}")
                else:
                    lines.append(f"- {item}")
        elif isinstance(value, dict):
            if not value:
                continue
            lines.append(f"\n**{label}**")
            for k, v in value.items():
                lines.append(f"- {k}: {v}")
        elif value not in (None, ""):
            lines.append(f"- **{label}:** {value}")

    return "\n".join(lines)


def _to_html(document_type: DocumentType, data: dict) -> str:
    body_parts = [f"<h2>{html.escape(document_type.value.title())}</h2>", "<dl>"]

    for key, value in data.items():
        label = html.escape(key.replace("_", " ").title())
        if isinstance(value, list):
            if not value:
                continue
            body_parts.append(f"<dt>{label}</dt><dd><ul>")
            for item in value:
                if isinstance(item, dict):
                    row = ", ".join(
                        f"{html.escape(str(k))}: {html.escape(str(v))}"
                        for k, v in item.items()
                        if v not in (None, "")
                    )
                    body_parts.append(f"<li>{row}</li>")
                else:
                    body_parts.append(f"<li>{html.escape(str(item))}</li>")
            body_parts.append("</ul></dd>")
        elif isinstance(value, dict):
            if not value:
                continue
            body_parts.append(f"<dt>{label}</dt><dd><ul>")
            for k, v in value.items():
                body_parts.append(f"<li>{html.escape(str(k))}: {html.escape(str(v))}</li>")
            body_parts.append("</ul></dd>")
        elif value not in (None, ""):
            body_parts.append(f"<dt>{label}</dt><dd>{html.escape(str(value))}</dd>")

    body_parts.append("</dl>")
    return _HTML_DOCUMENT_TEMPLATE.format(
        document_type=html.escape(document_type.value), body="\n".join(body_parts)
    )
