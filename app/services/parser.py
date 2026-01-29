import io
import magic
import docx
from pypdf import PdfReader
from fastapi import UploadFile

class UnsupportedContentTypeError(Exception):
    """Exception raised for unsupported file types."""
    def __init__(self, content_type: str):
        self.content_type = content_type
        super().__init__(f"Unsupported content type: {content_type}")

def _parse_docx(file_stream: io.BytesIO) -> str:
    """Parses a .docx file and returns its text content."""
    document = docx.Document(file_stream)
    return "\n".join([para.text for para in document.paragraphs])

def _parse_pdf(file_stream: io.BytesIO) -> str:
    """Parses a .pdf file and returns its text content."""
    reader = PdfReader(file_stream)
    return "\n".join([page.extract_text() for page in reader.pages])

async def parse_document(file: UploadFile) -> str:
    """
    Parses an uploaded file and extracts text content based on its MIME type.
    Supports plain text, DOCX, and PDF.
    """
    content = await file.read()
    
    # Reset stream position just in case
    await file.seek(0)
    
    # Use python-magic to determine the file type from its content
    mime_type = magic.from_buffer(content, mime=True)
    
    file_stream = io.BytesIO(content)

    if "text/plain" in mime_type:
        return content.decode("utf-8")
    elif "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in mime_type:
        return _parse_docx(file_stream)
    elif "application/pdf" in mime_type:
        return _parse_pdf(file_stream)
    else:
        raise UnsupportedContentTypeError(mime_type)
