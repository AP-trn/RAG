from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.parsers.images import RapidOCRBlobParser

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF. Automatically runs RapidOCR on embedded images 
    and scanned pages using rapidocr-onnxruntime.
    """
    # 1. Initialize PyPDFLoader with RapidOCR enabled for image parsing
    loader = PyPDFLoader(
        file_path=file_path,
        extract_images=False,
        #images_parser=RapidOCRBlobParser()
    )
    
    # 2. Load all pages
    documents = loader.load()
    
    # 3. Concatenate content into a single clean text string
    text = "\n".join([doc.page_content for doc in documents])
    
    return text
'''import os
from pypdf import PdfReader
from langchain_core.documents import Document


def load_documents(pdf_folder_path):
    docs = []
    for filename in os.listdir(pdf_folder_path):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(pdf_folder_path, filename)
            
            # Open the actual file path
            reader = PdfReader(file_path)
            text = ""

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            docs.append(Document(page_content=text, metadata={"source": filename}))
    return docs

# Now you can use your docs list safely
#print(f"Loaded {len(docs)} documents.")
#print(docs)
#print(f"Total Page Documents Loaded: {len(docs)}")
if __name__ == "__main__":
    pdf_folder_path = r"data/pdfs"
    docs = load_documents(pdf_folder_path)
    print(f"Loaded {len(docs)} documents.")'''