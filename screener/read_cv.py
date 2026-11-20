"""Turn a CV file into plain text, or explain clearly why we can't."""
from pathlib import Path

MIN_CHARS = 40  # fewer readable characters than this = nothing useful to screen


def read_cv(path: Path):
    """Return (text, error). Exactly one of them is None."""
    suffix = path.suffix.lower()
    try:
        if suffix in (".txt", ".md"):
            text = path.read_text(encoding="utf-8", errors="replace")
        elif suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            if len(text.strip()) < MIN_CHARS:
                return None, ("This PDF has no readable text (it looks like a scan or a photo). "
                              "Please ask the candidate for a text PDF, or paste the CV into a .txt file.")
        elif suffix in (".doc", ".docx"):
            return None, "Word files are not supported yet. Please save the CV as PDF (File > Save As > PDF) and try again."
        else:
            return None, f"Unsupported file type '{suffix}'. Please use .pdf or .txt files."
    except Exception as exc:  # corrupt or locked file
        return None, f"Could not open this file ({type(exc).__name__}). It may be damaged or still open in another program."

    if len(text.strip()) < MIN_CHARS:
        return None, "This file is empty or almost empty. Please check you uploaded the right CV."
    return text, None
