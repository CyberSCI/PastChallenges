import logging
import sys
import pytesseract
import fitz

from PIL import Image


logger = logging.getLogger(__name__)


LANGUAGE = 'eng'


def convert_pdf_to_image(pdf_path: str):
    try:
        with fitz.open(pdf_path) as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap()
            return pix.pil_image()
    except Exception as e:
        logger.error(f"Error converting PDF to image {pdf_path}: {e}")
        return None


def extract_text_from_image(image: Image):
    try:
        text = pytesseract.image_to_string(image, lang=LANGUAGE)
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from: {e}")
        return None

def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Document Scanner Module Initialized")
    
    if len(sys.argv) < 2:
        logger.error("Usage: python documentscanner.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    
    if image_path.endswith('.pdf'):
        logger.info(f"Converting PDF to image.")
        image = convert_pdf_to_image(image_path)
        if image is None:
            logger.error("Failed to convert PDF to image.")
            sys.exit(1)
    else:
        image = image_path
    
    logger.info(f"Extracting text from image.")
    extracted_text = extract_text_from_image(image)
    
    if extracted_text:
        print(extracted_text)


if __name__ == "__main__":
    main()