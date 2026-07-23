"""
Custom exceptions used across the application.

Keeping these distinct from generic Exceptions lets the FastAPI exception
handlers in main.py return clean, predictable JSON error responses instead
of leaking stack traces to the client.
"""


class AppException(Exception):
    """Base class for all application-specific exceptions."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UnsupportedFileTypeError(AppException):
    """Raised when an uploaded file's extension/mime-type is not supported."""

    def __init__(self, filename: str):
        super().__init__(
            message=f"Unsupported file type for '{filename}'. "
            f"Allowed types: PDF, PNG, JPG, JPEG, TIFF, BMP.",
            status_code=415,
        )


class FileTooLargeError(AppException):
    """Raised when an uploaded file exceeds the configured size limit."""

    def __init__(self, max_mb: int):
        super().__init__(
            message=f"File exceeds the maximum allowed size of {max_mb} MB.",
            status_code=413,
        )


class FileNotFoundInStorageError(AppException):
    """Raised when a referenced file_id cannot be located on disk."""

    def __init__(self, file_id: str):
        super().__init__(
            message=f"No uploaded file found with id '{file_id}'.",
            status_code=404,
        )


class OCREngineNotSupportedError(AppException):
    """Raised when an invalid OCR engine name is requested."""

    def __init__(self, engine_name: str):
        super().__init__(
            message=f"OCR engine '{engine_name}' is not supported.",
            status_code=422,
        )


class OutputFormatNotSupportedError(AppException):
    """Raised when an invalid output format is requested."""

    def __init__(self, output_format: str):
        super().__init__(
            message=f"Output format '{output_format}' is not supported.",
            status_code=422,
        )


class OCRProcessingError(AppException):
    """Raised when an OCR engine fails while processing a document."""

    def __init__(self, engine_name: str, detail: str):
        super().__init__(
            message=f"OCR processing failed using '{engine_name}': {detail}",
            status_code=500,
        )


class LLMServiceError(AppException):
    """
    Raised when a call to the LLM (classification or structured
    extraction) fails outright - e.g. no API key configured, network
    error, or a malformed response that couldn't be parsed as JSON.

    Callers in the extract pipeline catch this and fail soft, falling
    back to the plain OCR-formatted output rather than surfacing a 500.
    """

    def __init__(self, stage: str, detail: str):
        super().__init__(
            message=f"LLM {stage} failed: {detail}",
            status_code=502,
        )


class SchemaValidationError(AppException):
    """
    Raised when the LLM's structured extraction output fails Pydantic
    validation against the selected document schema (missing required
    fields, wrong types, etc.) after best-effort coercion.
    """

    def __init__(self, document_type: str, detail: str):
        super().__init__(
            message=f"Structured data for document type '{document_type}' "
            f"failed validation: {detail}",
            status_code=422,
        )
