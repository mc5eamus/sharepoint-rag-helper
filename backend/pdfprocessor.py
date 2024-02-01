from PyPDF2 import PdfReader
import requests
import io
import fitz
import numpy as np
import cv2
from filestorage import FileStorage
from model import DocumentFragment
from telemetry import get_logger

class PdfProcessor:

    def __init__(self, pdf_file_url: str, storage: FileStorage = None):
        self.pdf_file_url = pdf_file_url
        self.storage = storage

    @staticmethod
    def pix_to_image(pix):
        bytes = np.frombuffer(pix.samples, dtype=np.uint8)
        img = bytes.reshape(pix.height, pix.width, pix.n)
        return img
    
    @staticmethod
    def need_to_keep_image(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape 
        minLineLength = int((height + width) / 2 * 0.10)
        maxLineGap = 1
        edges = cv2.Canny(gray,0,100,apertureSize = 3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, minLineLength=minLineLength, maxLineGap=maxLineGap)
        if lines is None or len(lines) < 10:
            return False
        return True

    def split(self, prefix: str) -> [DocumentFragment]: 
        log = get_logger()
        log.info(f"Processing {self.pdf_file_url}")
        response = requests.get(self.pdf_file_url)
        pdf_io_bytes = io.BytesIO(response.content)
        
        doc = fitz.open(stream=pdf_io_bytes, filetype="pdf")
        # extract text from all pages
        for page in doc:
            text = page.get_text()
            pix = page.get_pixmap(matrix=fitz.Matrix(150/72,150/72))
            img = PdfProcessor.pix_to_image(pix)
            imageName = f"{prefix}-{page.number}.png"
            snapshot = None
            if self.storage is not None and self.need_to_keep_image(img):
                self.storage.put(cv2.imencode(".png", img)[1].tobytes(), imageName)
                snapshot = imageName
            
            yield DocumentFragment(
                text=text,
                snapshot=snapshot
            )