"""
Content Extractor for EPUB HTML files

This module provides intelligent content extraction that automatically detects
wrapper levels and groups content by headers for any EPUB publisher format.
"""

from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Optional
import os


def is_generic_header(element: Optional[Tag]) -> bool:
    """
    Identifies if an element is a header using tags, classes, and roles.

    Broadens detection beyond h1-h6 to support diverse writer styles.
    """
    if not element or not hasattr(element, 'name') or not element.name:
        return False

    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return True

    # Check common semantic roles
    if element.get('role') == 'heading':
        return True

    # Check class and ID for header-related keywords
    keywords = [
        'title', 'heading', 'chapter-head', 'ch-title', 'section-title',
        'chapter-label', 'ch-label', 'title-prefix', 'chapter-number',
        'label', 'title-text'
    ]

    # Combine class and ID for a single check
    class_attr = element.get('class')
    cls = " ".join(class_attr) if isinstance(class_attr, list) else (class_attr or "")
    id_val = element.get('id', '') or ""
    id_str = id_val if isinstance(id_val, str) else ""
    combined = (cls + " " + id_str).lower()

    if any(kw in combined for kw in keywords):
        # Additional safety: headers usually shouldn't be too long
        text = element.get_text(strip=True)
        if 0 < len(text) < 200:
            return True

    return False


def extract_content_sections(html_file_path: str) -> List[Dict[str, Any]]:
    """
    Extract content sections grouped by headers from HTML file.

    Uses generic header detection to support diverse publisher styles.

    Args:
        html_file_path: Path to HTML file to extract content from

    Returns:
        List of sections with header and content:
        [
            {
                'header': 'Chapter Title',
                'content': [list of content elements]
            },
            ...
        ]
    """
    if not os.path.exists(html_file_path):
        return []

    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            # Step 3.3: Try lxml-xml first for robustness with XHTML, then
            # fallback
            try:
                soup = BeautifulSoup(file, 'lxml-xml')
            except Exception:
                file.seek(0)
                soup = BeautifulSoup(file, 'html.parser')
    except Exception:
        return []

    body = soup.find('body')
    if not body:
        return []

    # Step 3.1: Selective tag stripping (boilerplate removal)
    for junk_tag in ['nav', 'aside', 'script', 'style', 'footer', 'header']:
        for junk in body.find_all(junk_tag):
            # Only decompose if it's not a generic header or doesn't contain
            # one
            if not is_generic_header(junk) and not any(
                    is_generic_header(c if isinstance(c, Tag) else None)
                    for c in junk.descendants if getattr(c, 'name', None)):
                junk.decompose()

    # Navigate to content level using child count logic
    current_container: Tag = body
    while True:
        children: List[Tag] = [
            child for child in current_container.children
            if isinstance(child, Tag) and child.name]

        # If only 1 child = wrapper, go deeper
        if len(children) == 1:
            current_container = children[0]
        else:
            # Multiple children = check if they are content or just wrapper containers
            # Look for headers as indication of content level
            header_tags: List[Tag] = [
                child for child in children if is_generic_header(child)]

            if len(header_tags) > 0:
                # Found headers, this is content level - stop here
                break
            elif len(children) > 0 and all(child.name in ['div', 'section', 'article'] for child in children):
                # All children are containers, need to check what's inside them
                break
            else:
                # Mixed content types, assume this is content level
                break

    # Get all content elements at this level
    content_children: List[Tag] = []
    if current_container:
        # Get all direct children (no filtering by tag type)
        all_direct_children: List[Tag] = [
            child for child in current_container.children
            if isinstance(child, Tag) and child.name]

        # Check if we have headers at this level
        direct_headers: List[Tag] = [
            child for child in all_direct_children if is_generic_header(child)]

        if direct_headers:
            # We have headers at this level, take ALL direct children as
            # content
            content_children = all_direct_children
        else:
            # No direct headers, check if children are containers that need to
            # be processed
            for child in all_direct_children:
                if child.name in ['div', 'section', 'article']:
                    # Check if this container has any children
                    child_elements: List[Tag] = [
                        subchild for subchild in child.children
                        if isinstance(subchild, Tag) and subchild.name]
                    if child_elements:
                        # Container has children, extract ALL of them
                        content_children.extend(child_elements)
                    else:
                        # Container has no children but might have text, treat
                        # as content
                        if child.get_text().strip():
                            content_children.append(child)
                else:
                    # Not a container, add directly
                    content_children.append(child)

    # Group by headers
    sections: List[Dict[str, Any]] = []
    current_header: Optional[str] = None
    current_content: List[Dict[str, Any]] = []
    current_images: List[str] = []

    for child in content_children:
        # Extract images from this child element
        child_images: List[str] = []
        # Standard img tags
        for img in child.find_all('img'):
            src = img.get('src')
            if src and isinstance(src, str):
                child_images.append(src)
        # SVG image tags
        for svg_img in child.find_all('image'):
            href = svg_img.get('href') or svg_img.get('xlink:href')
            if href and isinstance(href, str):
                child_images.append(href)
        # Check if the child itself is an image tag
        if child.name == 'img':
            src = child.get('src')
            if src and isinstance(src, str) and src not in child_images:
                child_images.append(src)
        elif child.name == 'image':
            href = child.get('href') or child.get('xlink:href')
            if href and isinstance(href, str) and href not in child_images:
                child_images.append(href)

        # Step 3.2: Filter out junk elements (boilerplate/link-heavy)
        generic_header = is_generic_header(child)
        if not generic_header:
            # Check link-to-text density
            text = child.get_text(strip=True)
            if len(text) > 40:  # Only check significant blocks
                links_text = "".join([a.get_text(strip=True)
                                     for a in child.find_all('a')])
                if (len(links_text) / len(text)) > 0.70:
                    # Likely a menu or breadcrumb block - skip
                    continue

            # Skip completely empty blocks that have no images
            if not text and not child_images:
                continue

        if generic_header:
            # Save previous section before starting new one
            if current_header or current_content:
                sections.append({
                    'header': current_header or 'Intro',
                    'content': current_content,
                    'images': current_images
                })
            # Start new section
            current_header = child.get_text().strip()
            current_content = [{
                'tag': child.name,
                'text': current_header,
                'html': str(child),
                'images': child_images,
                'is_header': True
            }]
            current_images = child_images  # Images in the header itself
        else:
            # Add to current section
            current_content.append({
                'tag': child.name,
                'text': child.get_text().strip(),
                'html': str(child),
                'images': child_images
            })
            current_images.extend(child_images)

    # Add final section
    if current_header or current_content:
        sections.append({
            'header': current_header or 'Intro',
            'content': current_content,
            'images': current_images
        })

    return sections


def extract_book_content(epub_directory_path: str) -> Dict[str, Any]:
    """
    Extract content from all HTML files in an EPUB directory.

    Args:
        epub_directory_path: Path to extracted EPUB directory

    Returns:
        Dictionary with file paths and their extracted content sections
    """
    content_data = {}

    # Process all HTML files in the directory recursively
    # This is more robust than looking specifically for 'OEBPS'
    for root, dirs, files in os.walk(epub_directory_path):
        # Skip some common non-content directories
        if any(skip in root for skip in ['META-INF', '__MACOSX', '.git']):
            continue

        for file in files:
            if file.endswith(('.html', '.xhtml', '.htm')):
                file_path = os.path.join(root, file)
                # Path relative to the EPUB root
                relative_path = os.path.relpath(file_path, epub_directory_path)

                sections = extract_content_sections(file_path)
                if sections:
                    # Step 1.3: Resolve image paths to be "absolute-in-epub"
                    # (relative to root)
                    html_rel_dir = os.path.dirname(relative_path)

                    for section in sections:
                        # 1. Resolve section-level images
                        resolved_section_images = []
                        for img_src in section.get('images', []):
                            if img_src.startswith(('http://', 'https://')):
                                resolved_section_images.append(img_src)
                                continue
                            base_img_src = img_src.split('#')[0]
                            resolved_path = os.path.normpath(
                                os.path.join(html_rel_dir, base_img_src))
                            if resolved_path.startswith('..'):
                                resolved_path = resolved_path.replace(
                                    '../', '').lstrip('/')
                            if resolved_path not in resolved_section_images:
                                resolved_section_images.append(resolved_path)
                        section['images'] = resolved_section_images

                        # 2. Resolve element-level images (new)
                        for block in section.get('content', []):
                            resolved_block_images = []
                            for img_src in block.get('images', []):
                                if img_src.startswith(('http://', 'https://')):
                                    resolved_block_images.append(img_src)
                                    continue
                                base_img_src = img_src.split('#')[0]
                                resolved_path = os.path.normpath(
                                    os.path.join(html_rel_dir, base_img_src))
                                if resolved_path.startswith('..'):
                                    resolved_path = resolved_path.replace(
                                        '../', '').lstrip('/')
                                if resolved_path not in resolved_block_images:
                                    resolved_block_images.append(resolved_path)
                            block['images'] = resolved_block_images

                    content_data[relative_path] = sections

    return content_data
