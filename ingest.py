"""
ingest.py  —  STEP 1 of RAG: build the knowledge base.

What this does (the "Retrieval" half of RAG):
  1. Reads every .txt and .pdf file in the data/ folder.
  2. Splits the text into small overlapping "chunks".
  3. Turns each chunk into an embedding (a vector of numbers) using a
     sentence-transformer model.
  4. Stores the chunks + vectors in a ChromaDB vector database on disk.

Run it once (and again whenever you change your data):
    python ingest.py
"""

import os
import glob
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

DATA_DIR = "data"
DB_DIR = "chroma_db"
COLLECTION_NAME = "knowledge_base"

# all-MiniLM-L6-v2: small, fast, free, runs locally. 384-dimensional vectors.
EMBED_MODEL = "all-MiniLM-L6-v2"

# --- Chunking settings -------------------------------------------------------
# Chunks must be small enough to be specific, big enough to keep context.
CHUNK_SIZE_WORDS = 180      # ~1 paragraph
CHUNK_OVERLAP_WORDS = 40    # repeat some words so ideas aren't cut in half


def read_file(path: str) -> str:
    """Return the plain text of a .txt or .pdf file."""
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping word-windows."""
    words = text.split()
    chunks = []
    step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS
    for start in range(0, len(words), step):
        window = words[start:start + CHUNK_SIZE_WORDS]
        if not window:
            break
        chunk = " ".join(window).strip()
        if len(chunk) > 30:            # skip tiny leftovers
            chunks.append(chunk)
        if start + CHUNK_SIZE_WORDS >= len(words):
            break
    return chunks


def main():
    files = glob.glob(os.path.join(DATA_DIR, "*.txt")) + \
            glob.glob(os.path.join(DATA_DIR, "*.pdf"))
    if not files:
        print(f"No .txt or .pdf files found in '{DATA_DIR}/'. Add your dataset there.")
        return

    # The embedding function turns text -> vectors. Chroma calls it for us.
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )

    client = chromadb.PersistentClient(path=DB_DIR)
    # Start fresh each run so re-ingesting doesn't create duplicates.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},   # use cosine similarity for search
    )

    total = 0
    for path in files:
        text = read_file(path)
        chunks = chunk_text(text)
        if not chunks:
            print(f"  (skipped, no text) {path}")
            continue
        source = os.path.basename(path)
        ids = [f"{source}::chunk{i}" for i in range(len(chunks))]
        metadatas = [{"source": source, "chunk": i} for i in range(len(chunks))]
        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        total += len(chunks)
        print(f"  + {source}: {len(chunks)} chunks")

    print(f"\nDone. Stored {total} chunks from {len(files)} file(s) in '{DB_DIR}/'.")


if __name__ == "__main__":
    main()
