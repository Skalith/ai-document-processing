"""Prompt template for Step 6: structured extraction of resume documents."""

from __future__ import annotations

_RESUME_JSON_SHAPE = """{
  "full_name": "",
  "email": null,
  "phone": null,
  "location": null,
  "summary": null,
  "skills": [],
  "experience": [
    {"company": "", "title": "", "start_date": null, "end_date": null, "description": null}
  ],
  "education": [
    {"institution": "", "degree": null, "field_of_study": null, "start_date": null, "end_date": null}
  ]
}"""


def build_resume_extraction_prompt(raw_text: str) -> str:
    return (
        "Extract the resume/CV details from the following document text "
        "into this exact JSON shape (fill in real values, keep the same "
        "keys):\n\n"
        f"{_RESUME_JSON_SHAPE}\n\n"
        "Document text:\n"
        "---\n"
        f"{raw_text.strip()}\n"
        "---\n\n"
        "Respond with ONLY the JSON object."
    )
