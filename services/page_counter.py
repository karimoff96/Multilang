import os
import mimetypes
from django.conf import settings
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import magic


def get_file_type(file_path):
    """Get file type using python-magic"""
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except:
        return mimetypes.guess_type(file_path)[0]


def count_pdf_pages(file_path):
    """Count pages in PDF file"""
    try:
        with open(file_path, "rb") as file:
            pdf_reader = PdfReader(file)
            return len(pdf_reader.pages)
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return 1


def count_docx_pages(file_path):
    """Count pages in DOCX file"""
    try:
        doc = Document(file_path)
        # Count paragraphs and estimate pages (rough estimate)
        paragraphs = len([p for p in doc.paragraphs if p.text.strip()])
        # Assuming ~50 paragraphs per page as rough estimate
        pages = max(1, paragraphs // 50)
        return pages
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return 1


def count_image_pages(file_path):
    """Images are considered as 1 page each"""
    try:
        # Just check if it's a valid image
        Image.open(file_path).verify()
        return 1
    except Exception as e:
        print(f"Error reading image {file_path}: {e}")
        return 1


def count_text_file_pages(file_path):
    """Count pages in text files"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
            lines = len(content.split("\n"))
            # Assuming ~60 lines per page
            pages = max(1, lines // 60)
            return pages
    except Exception as e:
        print(f"Error reading text file {file_path}: {e}")
        return 1


def count_file_pages(file_path):
    """Count pages in a file based on its type"""
    if not os.path.exists(file_path):
        return 1

    mime_type = get_file_type(file_path)

    if mime_type:
        if "pdf" in mime_type.lower():
            return count_pdf_pages(file_path)
        elif "document" in mime_type.lower() or "word" in mime_type.lower():
            if file_path.lower().endswith(".docx"):
                return count_docx_pages(file_path)
            else:
                return 1  # DOC files are harder to process
        elif "image" in mime_type.lower():
            return count_image_pages(file_path)
        elif "text" in mime_type.lower():
            return count_text_file_pages(file_path)

    # Fallback based on file extension
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return count_pdf_pages(file_path)
    elif extension == ".docx":
        return count_docx_pages(file_path)
    elif extension in [".doc", ".txt", ".rtf"]:
        return count_text_file_pages(file_path)
    elif extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
        return count_image_pages(file_path)
    else:
        # Unknown file type, assume 1 page
        return 1


def count_pages_from_uploaded_file(uploaded_file):
    """Count pages from a Django uploaded file"""
    import tempfile

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
    ) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    try:
        pages = count_file_pages(temp_file_path)
        return pages
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
