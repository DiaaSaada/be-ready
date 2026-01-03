"""
File parsing service for extracting text from uploaded documents.
Supports PDF, DOCX, and TXT formats.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# PDF parsing
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pypdf2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        HAS_PYPDF2 = True
    except ImportError:
        HAS_PYPDF2 = False

# DOCX parsing
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


@dataclass
class ParsedFile:
    """Result of parsing a single file."""
    filename: str
    file_type: str
    content: str
    char_count: int
    page_count: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class ParseResult:
    """Aggregated result of parsing multiple files."""
    files: List[ParsedFile]
    combined_content: str
    total_chars: int
    successful_count: int
    failed_count: int
    errors: List[Dict[str, str]]


class FileParserService:
    """Service for parsing uploaded files and extracting text."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def parse_pdf(self, file_path: Path) -> ParsedFile:
        """
        Extract text from PDF using PyMuPDF (primary) with PyPDF2 fallback.
        """
        filename = file_path.name

        # Try PyMuPDF first (better extraction quality)
        if HAS_PYMUPDF:
            try:
                doc = fitz.open(str(file_path))
                text_parts = []
                for page in doc:
                    text_parts.append(page.get_text())
                content = "\n".join(text_parts)
                page_count = len(doc)
                doc.close()

                return ParsedFile(
                    filename=filename,
                    file_type="pdf",
                    content=content.strip(),
                    char_count=len(content),
                    page_count=page_count
                )
            except Exception as e:
                self.logger.warning(f"PyMuPDF failed for {filename}: {e}")
                # Fall through to PyPDF2

        # Fallback to PyPDF2
        if HAS_PYPDF2:
            try:
                reader = PdfReader(str(file_path))
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                content = "\n".join(text_parts)

                return ParsedFile(
                    filename=filename,
                    file_type="pdf",
                    content=content.strip(),
                    char_count=len(content),
                    page_count=len(reader.pages)
                )
            except Exception as e:
                self.logger.error(f"PyPDF2 failed for {filename}: {e}")
                return ParsedFile(
                    filename=filename,
                    file_type="pdf",
                    content="",
                    char_count=0,
                    success=False,
                    error=f"PDF parsing failed: {str(e)}"
                )

        return ParsedFile(
            filename=filename,
            file_type="pdf",
            content="",
            char_count=0,
            success=False,
            error="No PDF parsing library available"
        )

    async def parse_docx(self, file_path: Path) -> ParsedFile:
        """Extract text from DOCX using python-docx."""
        filename = file_path.name

        if not HAS_DOCX:
            return ParsedFile(
                filename=filename,
                file_type="docx",
                content="",
                char_count=0,
                success=False,
                error="python-docx library not available"
            )

        try:
            doc = Document(str(file_path))
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            content = "\n".join(paragraphs)

            return ParsedFile(
                filename=filename,
                file_type="docx",
                content=content.strip(),
                char_count=len(content)
            )
        except Exception as e:
            self.logger.error(f"DOCX parsing failed for {filename}: {e}")
            return ParsedFile(
                filename=filename,
                file_type="docx",
                content="",
                char_count=0,
                success=False,
                error=f"DOCX parsing failed: {str(e)}"
            )

    async def parse_txt(self, file_path: Path) -> ParsedFile:
        """Read text from TXT file with multiple encoding support."""
        filename = file_path.name
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return ParsedFile(
                    filename=filename,
                    file_type="txt",
                    content=content.strip(),
                    char_count=len(content)
                )
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.error(f"TXT parsing failed for {filename}: {e}")
                return ParsedFile(
                    filename=filename,
                    file_type="txt",
                    content="",
                    char_count=0,
                    success=False,
                    error=f"Text file reading failed: {str(e)}"
                )

        return ParsedFile(
            filename=filename,
            file_type="txt",
            content="",
            char_count=0,
            success=False,
            error="Could not decode text file with supported encodings"
        )

    async def parse_file(self, file_path: Path) -> ParsedFile:
        """Parse a single file based on its extension."""
        ext = file_path.suffix.lower()

        if ext == ".pdf":
            return await self.parse_pdf(file_path)
        elif ext == ".docx":
            return await self.parse_docx(file_path)
        elif ext == ".txt":
            return await self.parse_txt(file_path)
        else:
            return ParsedFile(
                filename=file_path.name,
                file_type="unknown",
                content="",
                char_count=0,
                success=False,
                error=f"Unsupported file type: {ext}"
            )

    async def parse_files(self, file_paths: List[Path]) -> ParseResult:
        """
        Parse multiple files and aggregate results.

        Combines content from all successfully parsed files,
        separated by file headers.
        """
        parsed_files = []
        errors = []

        for file_path in file_paths:
            result = await self.parse_file(file_path)
            parsed_files.append(result)

            if not result.success:
                errors.append({
                    "filename": result.filename,
                    "error": result.error or "Unknown error"
                })

        # Combine successful content with file separators
        successful_files = [f for f in parsed_files if f.success and f.content.strip()]
        combined_parts = []

        for f in successful_files:
            combined_parts.append(f"=== Content from: {f.filename} ===\n{f.content}")

        combined_content = "\n\n".join(combined_parts)

        return ParseResult(
            files=parsed_files,
            combined_content=combined_content,
            total_chars=len(combined_content),
            successful_count=len(successful_files),
            failed_count=len(errors),
            errors=errors
        )


# Singleton instance
_file_parser: Optional[FileParserService] = None


def get_file_parser() -> FileParserService:
    """Get or create the file parser service instance."""
    global _file_parser
    if _file_parser is None:
        _file_parser = FileParserService()
    return _file_parser
