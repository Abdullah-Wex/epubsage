"""EPUB structure validation utilities."""

import zipfile
from typing import Dict, List, Any


def validate_epub_structure(epub_path: str) -> Dict[str, Any]:
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
                mimetype_info = zip_ref.getinfo('mimetype')
                if mimetype_info.compress_type != zipfile.ZIP_STORED:
                    warnings.append("mimetype file should be uncompressed")
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
