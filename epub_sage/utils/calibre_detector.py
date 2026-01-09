"""Calibre EPUB detection utility."""


def is_calibre_generated(content_opf_path: str) -> bool:
    """
    Detect if EPUB was generated/processed by Calibre.

    Calibre adds signature metadata:
    - <dc:contributor opf:role="bkp">calibre (X.Y.Z)</dc:contributor>
    - <meta name="calibre:timestamp">
    - calibre.kovidgoyal.net namespace

    Args:
        content_opf_path: Path to content.opf file

    Returns:
        True if Calibre-generated, False otherwise
    """
    try:
        with open(content_opf_path, 'r', encoding='utf-8') as f:
            content = f.read(4096)  # Check first 4KB only

        calibre_signatures = [
            'calibre.kovidgoyal.net',
            'name="calibre:',
            'opf:role="bkp">calibre',
        ]
        return any(sig in content for sig in calibre_signatures)
    except Exception:
        return False
