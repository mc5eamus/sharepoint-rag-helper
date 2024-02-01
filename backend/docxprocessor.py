import docx
import requests
import io
import tiktoken
from model import DocumentFragment

class DocxProcessor:
    """
    Processes a docx file by splitting it into fragments of a given token limit.
    TODO: introduce overlap between fragments to avoid cutting through words and sentences
    """
    def __init__(self, docx_file_url, token_limit:int = 1000):
        self.docx_file_url = docx_file_url
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.token_limit = token_limit

    def split(self, prefix: str) -> [DocumentFragment]: 
        response = requests.get(self.docx_file_url)
        docx_io_bytes = io.BytesIO(response.content)
        doc = docx.Document(docx_io_bytes)
        current_block = ""
        current_token_count = 0
        para_len = 0
        for para in doc.paragraphs:
            para_len = len(self.encoding.encode(para.text))
            if para_len == 0:
                continue
            if current_token_count + para_len > self.token_limit:
                yield DocumentFragment( text=current_block, snapshot=None )
                current_block = ""
                current_token_count = 0
            current_block += para.text + "\n"
            current_token_count += para_len
        if current_token_count > 0:
            yield DocumentFragment( text=current_block, snapshot=None)
        
        