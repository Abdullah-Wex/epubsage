"""
EPUB File Extractor - ZIP file extraction and management.

Provides essential EPUB file handling that was missing from parse_service.
Adapted from Epub_service with enhancements.
"""
import zipfile
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Any


class EpubExtractor:
    """
    Handles EPUB file extraction and management.

    This class provides the critical ZIP extraction functionality that
    parse_service was missing, enabling it to process .epub files directly.
    """

    def __init__(self, base_dir: str = "uploads"):
        """
        Initialize EPUB extractor.

        Args:
            base_dir: Base directory for extracting EPUB files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def extract_epub(
            self,
            epub_path: str,
            output_dir: Optional[str] = None) -> str:
        """
        Extract EPUB file to organized directory structure.

        Args:
            epub_path: Path to EPUB file
            output_dir: Optional custom output directory

        Returns:
            Path to extracted directory

        Raises:
            FileNotFoundError: If EPUB file doesn't exist
            ValueError: If file is not a valid ZIP/EPUB
        """
        epub_file = Path(epub_path)
        if not epub_file.exists():
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        # Generate unique book ID from file hash
        book_id = self.generate_book_id(epub_path)

        # Determine extraction directory
        if output_dir:
            extract_dir = Path(output_dir)
        else:
            extract_dir = self.base_dir / book_id / "raw"

        extract_dir.mkdir(parents=True, exist_ok=True)

        # Extract ZIP file
        try:
            with zipfile.ZipFile(epub_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile:
            raise ValueError(f"Invalid ZIP/EPUB file: {epub_file}")

        return str(extract_dir)

    def generate_book_id(self, file_path: str) -> str:
        """
        Generate unique book ID from file hash.

        Args:
            file_path: Path to EPUB file

        Returns:
            16-character hash string
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:16]

    def get_epub_info(self, epub_path: str) -> Dict[str, Any]:
        """
        Get EPUB information without extracting.

        Args:
            epub_path: Path to EPUB file

        Returns:
            Dictionary with file info
        """
        epub_file = Path(epub_path)
        if not epub_file.exists():
            return {"error": "File not found", "success": False}

        try:
            with zipfile.ZipFile(epub_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_size = sum(
                    zip_ref.getinfo(name).file_size for name in file_list)

                # Check for content.opf
                content_opf_path = None
                for name in file_list:
                    if name.endswith('content.opf'):
                        content_opf_path = name
                        break

                # Count file types
                html_files = [
                    f for f in file_list if f.endswith(
                        ('.html', '.xhtml', '.htm'))]
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
        """
        Clean up extracted EPUB directory.

        Args:
            extracted_dir: Path to extracted directory

        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if Path(extracted_dir).exists():
                shutil.rmtree(extracted_dir)
                return True
            return False
        except Exception:
            return False

    def list_epub_contents(self, epub_path: str) -> List[str]:
        """
        List contents of EPUB file without extracting.

        Args:
            epub_path: Path to EPUB file

        Returns:
            List of file paths in the EPUB
        """
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
        """
        Extract a single file from EPUB.

        Args:
            epub_path: Path to EPUB file
            file_path: Path of file inside EPUB to extract
            output_path: Where to save the extracted file

        Returns:
            True if extraction successful
        """
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                with zip_ref.open(file_path) as source:
                    with open(output_path, 'wb') as target:
                        target.write(source.read())
                return True
        except BaseException:
            return False

    def find_content_opf(self, extracted_dir: str) -> Optional[str]:
        """
        Find content.opf file in extracted EPUB directory.

        Args:
            extracted_dir: Path to extracted EPUB

        Returns:
            Path to content.opf file or None if not found
        """
        base_path = Path(extracted_dir)

        # Common locations for content.opf
        common_paths = [
            base_path / "content.opf",
            base_path / "OEBPS" / "content.opf",
            base_path / "OPS" / "content.opf",
        ]

        # Check common locations first
        for opf_path in common_paths:
            if opf_path.exists():
                return str(opf_path)

        # Search recursively as fallback
        for opf_file in base_path.rglob("*.opf"):
            return str(opf_file)

        return None

    def validate_epub_structure(self, epub_path: str) -> Dict[str, Any]:
        """
        Validate EPUB file structure and requirements.

        Args:
            epub_path: Path to EPUB file

        Returns:
            Validation results dictionary
        """
        errors: List[str] = []
        warnings: List[str] = []
        results: Dict[str, Any] = {
            "is_valid": False,
            "has_mimetype": False,
            "has_container_xml": False,
            "has_content_opf": False,
            "errors": errors,
            "warnings": warnings
        }

        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()

                # Check for mimetype
                if 'mimetype' in file_list:
                    results["has_mimetype"] = True
                    # Check if mimetype is first and uncompressed
                    mimetype_info = zip_ref.getinfo('mimetype')
                    if mimetype_info.compress_type != zipfile.ZIP_STORED:
                        warnings.append(
                            "mimetype file should be uncompressed")
                else:
                    errors.append("Missing mimetype file")

                # Check for META-INF/container.xml
                if 'META-INF/container.xml' in file_list:
                    results["has_container_xml"] = True
                else:
                    errors.append("Missing META-INF/container.xml")

                # Check for content.opf
                for name in file_list:
                    if name.endswith('content.opf'):
                        results["has_content_opf"] = True
                        break

                if not results["has_content_opf"]:
                    errors.append("Missing content.opf file")

                # Determine validity
                results["is_valid"] = (
                    results["has_mimetype"] and
                    results["has_container_xml"] and
                    results["has_content_opf"]
                )

                return results

        except zipfile.BadZipFile:
            errors.append("Not a valid ZIP file")
            return results
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return results


def quick_extract(epub_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convenience function for quick EPUB extraction.

    Args:
        epub_path: Path to EPUB file
        output_dir: Optional output directory

    Returns:
        Path to extracted directory
    """
    extractor = EpubExtractor()
    return extractor.extract_epub(epub_path, output_dir)


def get_epub_info(epub_path: str) -> Dict[str, Any]:
    """
    Convenience function to get EPUB info without extraction.

    Args:
        epub_path: Path to EPUB file

    Returns:
        Dictionary with EPUB information
    """
    extractor = EpubExtractor()
    return extractor.get_epub_info(epub_path)
