import uuid
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chonkie import SemanticChunker

def recursive_chunking(text: str, filename: str) -> tuple[list[Document], list[str]]:
    """Strategy 1: Standard Recursive Character Splitting."""
    doc = Document(page_content=text, metadata={"source": filename})
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents([doc])
    chunk_ids = [f"{filename}_{i}" for i in range(len(chunks))]
    return chunks, chunk_ids

def semantic_chunking(text: str, filename: str, embeddings) -> tuple[list[Document], list[str]]:
    """Strategy 2: Semantic Chunker based on sentence similarity."""
    doc = Document(page_content=text, metadata={"source": filename})
    splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
    chunks = splitter.split_documents([doc])
    chunk_ids = [f"{filename}_{i}" for i in range(len(chunks))]
    return chunks, chunk_ids

def parent_child_chunking(text: str, filename: str) -> tuple[list[Document], list[Document]]:
    """Strategy 3: Hierarchical Chunking (Large Parent Context, Small Child Vectors)."""
    doc = Document(page_content=text, metadata={"source": filename})
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    
    parents = parent_splitter.split_documents([doc])
    children = []
    for parent in parents:
        sub_docs = child_splitter.split_documents([parent])
        for child in sub_docs:
            child.metadata["parent_id"] = str(uuid.uuid4())
            children.append(child)
            
    return parents, children