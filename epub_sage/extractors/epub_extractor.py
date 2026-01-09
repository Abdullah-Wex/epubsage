"""EPUB File Extractor - ZIP file extraction and management."""

import zipfile
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Any

from .epub_validator import validate_epub_structure


class EpubExtractor:
    """Handles EPUB file extraction and management."""

    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def extract_epub(
            self,
            epub_path: str,
            output_dir: Optional[str] = None) -> str:
        """Extract EPUB file to organized directory structure."""
        epub_file = Path(epub_path)
        if not epub_file.exists():
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        book_id = self.generate_book_id(epub_path)

        if output_dir:
            extract_dir = Path(output_dir)
        else:
            extract_dir = self.base_dir / book_id / "raw"

        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(epub_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile:
            raise ValueError(f"Invalid ZIP/EPUB file: {epub_file}")

        return str(extract_dir)

    def generate_book_id(self, file_path: str) -> str:
        """Generate unique book ID from file hash."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:16]

    def get_epub_info(self, epub_path: str) -> Dict[str, Any]:
        """Get EPUB information without extracting."""
        epub_file = Path(epub_path)
        if not epub_file.exists():
            return {"error": "File not found", "success": False}

        try:
            with zipfile.ZipFile(epub_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_size = sum(
                    zip_ref.getinfo(name).file_size for name in file_list)

                content_opf_path = None
                for name in file_list:
                    if name.endswith('content.opf'):
                        content_opf_path = name
                        break

                html_files = [
                    f for f in file_list if f.endswith(('.html', '.xhtml', '.htm'))]
                image_files = [
                    f for f in file_list if f.endswith(
                        ('.jpg', '.jpeg', '.png', '.gif', '.svg'))]
                css_files = [f for f in file_list if f.endswith('.css')]

                return {
                    "book_id": self.generate_book_id(epub_path),
                    "filename": epub_file.name,
                    "total_files": len(file_list),
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "content_opf": content_opf_path,
                    "html_files_count": len(html_files),
                    "image_files_count": len(image_files),
                    "css_files_count": len(css_files),
                    "is_valid_epub": content_opf_path is not None,
                    "success": True
                }
        except zipfile.BadZipFile:
            return {"error": "Invalid ZIP/EPUB file", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def cleanup_extraction(self, extracted_dir: str) -> bool:
        """Clean up extracted EPUB directory."""
        try:
            if Path(extracted_dir).exists():
                shutil.rmtree(extracted_dir)
                return True
            return False
        except Exception:
            return False

    def list_epub_contents(self, epub_path: str) -> List[str]:
        """List contents of EPUB file without extracting."""
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                return zip_ref.namelist()
        except BaseException:
            return []

    def extract_single_file(
            self,
            epub_path: str,
            file_path: str,
            output_path: str) -> bool:
        """Extract a single file from EPUB."""
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                with zip_ref.open(file_path) as source:
                    with open(output_path, 'wb') as target:
                        target.write(source.read())
                return True
        except BaseException:
            return False

    def find_content_opf(self, extracted_dir: str) -> Optional[str]:
        """Find content.opf file in extracted EPUB directory."""
        base_path = Path(extracted_dir)

        common_paths = [
            base_path / "content.opf",
            base_path / "OEBPS" / "content.opf",
            base_path / "OPS" / "content.opf",
        ]

        for opf_path in common_paths:
            if opf_path.exists():
                return str(opf_path)

        for opf_file in base_path.rglob("*.opf"):
            return str(opf_file)

        return None

    def validate_epub_structure(self, epub_path: str) -> Dict[str, Any]:
        """Validate EPUB file structure and requirements."""
        return validate_epub_structure(epub_path)


def quick_extract(epub_path: str, output_dir: Optional[str] = None) -> str:
    """Convenience function for quick EPUB extraction."""
    extractor = EpubExtractor()
    return extractor.extract_epub(epub_path, output_dir)


def get_epub_info(epub_path: str) -> Dict[str, Any]:
    """Convenience function to get EPUB info without extraction."""
    extractor = EpubExtractor()
    return extractor.get_epub_info(epub_path)
