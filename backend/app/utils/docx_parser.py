from docx import Document


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts)
