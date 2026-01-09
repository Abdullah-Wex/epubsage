"""Image path resolution for EPUB content extraction."""

import os
from typing import List, Optional, Set

# Common EPUB image extensions
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')

# External URL prefixes
EXTERNAL_PREFIXES = ('http://', 'https://', 'data:')


def is_external_url(path: str) -> bool:
    """Check if path is an external URL."""
    return path.startswith(EXTERNAL_PREFIXES)


def normalize_path(path: str) -> str:
    """Normalize path separators and handle parent refs."""
    normalized = path.replace('\\', '/')
    while normalized.startswith('../'):
        normalized = normalized[3:]
    return normalized


def discover_epub_images(epub_directory_path: str) -> Set[str]:
    """Discover all image files in an EPUB directory."""
    image_paths: Set[str] = set()

    for root, _, files in os.walk(epub_directory_path):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, epub_directory_path)
                image_paths.add(normalize_path(relative_path))

    return image_paths


def resolve_image_path(img_src: str, html_rel_dir: str) -> Optional[str]:
    """Resolve a relative image path to EPUB-root-relative path."""
    if is_external_url(img_src):
        return img_src

    base_src = img_src.split('#')[0].split('?')[0]
    if not base_src:
        return None

    resolved = os.path.normpath(os.path.join(html_rel_dir, base_src))
    return normalize_path(resolved)


def resolve_and_validate_images(
    raw_images: List[str],
    html_rel_dir: str,
    valid_images: Set[str]
) -> List[str]:
    """Resolve image paths and filter to only those that exist in EPUB."""
    seen: Set[str] = set()
    result: List[str] = []

    for img_src in raw_images:
        resolved = resolve_image_path(img_src, html_rel_dir)
        if not resolved or resolved in seen:
            continue

        if is_external_url(resolved) or resolved in valid_images:
            seen.add(resolved)
            result.append(resolved)

    return result
