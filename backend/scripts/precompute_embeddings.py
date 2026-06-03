"""
Precompute embeddings for candidate resumes and ingest into ChromaDB.
- Uses GPU if available (torch.cuda.is_available()).
- Saves embeddings to `backend/data/embeddings/resume_embeddings.npy` and ids.
- Creates/updates ChromaDB collection `candidates` with embeddings and metadata.

Run:
    python backend/scripts/precompute_embeddings.py --batch 64 --limit 0

Options:
  --batch N    Batch size for embeddings (default 64)
  --limit M    Limit number of rows to process (0 = all)
"""

import argparse
import os
import json
from typing import List

import numpy as np
import pandas as pd

import chromadb

from sentence_transformers import SentenceTransformer
import torch


def load_dataset(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")


def get_device():
    if torch.cuda.is_available():
        return "cuda"
    # else try mps for mac, else cpu
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def compute_embeddings(model, texts: List[str], batch_size: int = 64):
    embs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = model.encode(batch, show_progress_bar=False)
        embs.append(emb)
    return np.vstack(embs)


def ingest_to_chroma(client, ids: List[str], embeddings: List[List[float]], metadatas: List[dict], documents: List[str]):
    try:
        client.delete_collection(name="candidates")
    except Exception:
        pass

    coll = client.get_or_create_collection(
        name="candidates",
        metadata={"hnsw:space": "cosine"},
    )

    # Chroma imposes a max batch size; add in chunks to avoid errors.
    max_chunk = 5000
    n = len(ids)
    for start in range(0, n, max_chunk):
        end = min(start + max_chunk, n)
        chunk_ids = ids[start:end]
        chunk_emb = embeddings[start:end]
        chunk_meta = metadatas[start:end]
        chunk_docs = documents[start:end]
        print(f"Adding chunk {start}:{end} (size={len(chunk_ids)})...")
        try:
            coll.add(ids=chunk_ids, metadatas=chunk_meta, documents=chunk_docs, embeddings=chunk_emb)
            print(f"  Chunk {start}:{end} added successfully.")
        except Exception as e:
            print(f"  Error adding chunk {start}:{end}: {e}")
            # If add fails (e.g., duplicate ids), try to handle by removing existing ids then retry
            try:
                existing = []
                try:
                    existing = coll.get(ids=chunk_ids).get("ids", [])
                except Exception:
                    existing = []
                if existing:
                    print(f"  Deleting {len(existing)} existing ids in chunk {start}:{end} and retrying...")
                    coll.delete(ids=existing)
                coll.add(ids=chunk_ids, metadatas=chunk_meta, documents=chunk_docs, embeddings=chunk_emb)
                print(f"  Chunk {start}:{end} added after deleting duplicates.")
            except Exception as e2:
                print(f"  Warning: failed to add chunk {start}:{end} after retry -> {e2}")
    return coll


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    BASE = os.path.join(os.path.dirname(__file__), "..", "..")
    DATA_CSV = os.path.join(BASE, "backend", "data", "job_applicant_dataset_final.csv")
    EMB_DIR = os.path.join(BASE, "backend", "data", "embeddings")
    os.makedirs(EMB_DIR, exist_ok=True)

    print("Loading dataset:", DATA_CSV)
    df = load_dataset(DATA_CSV)
    if args.limit and args.limit > 0:
        df = df.head(args.limit)

    texts = df["Resume"].fillna("").astype(str).tolist()
    ids = [f"cand_{i}" for i in range(len(df))]
    documents = df["Resume"].fillna("").astype(str).tolist()
    metadatas = []
    for i, row in df.iterrows():
        metadatas.append({
            "index": int(i),
            "name": str(row.get("Job Applicant Name", "")),
            "job_roles": row.get("Job Roles", ""),
            "years_experience": row.get("años de experiencia", None),
            "salary": row.get("sueldo pretendido", None)
        })

    # If embeddings were already saved previously, load them to avoid recomputing
    emb_path = os.path.join(EMB_DIR, "resume_embeddings.npy")
    ids_path = os.path.join(EMB_DIR, "ids.json")
    if os.path.exists(emb_path) and os.path.exists(ids_path) and not args.limit:
        print("Found existing embeddings on disk, loading...")
        embeddings = np.load(emb_path)
        with open(ids_path, "r", encoding="utf-8") as f:
            ids = json.load(f)
        print("Embeddings loaded. Shape:", embeddings.shape)
    else:
        device = get_device()
        print(f"Using device: {device}")

        model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        print("Model loaded.")

        print(f"Computing embeddings in batches of {args.batch} for {len(texts)} items...")
        embeddings = compute_embeddings(model, texts, batch_size=args.batch)
        print("Embeddings computed. Shape:", embeddings.shape)

        # Save embeddings and ids
        np.save(emb_path, embeddings)
        with open(ids_path, "w", encoding="utf-8") as f:
            json.dump(ids, f, ensure_ascii=False)

        print("Embeddings saved to disk.")

    # Ingest into ChromaDB
    persist_dir = os.path.join(BASE, "data", "chroma_db")
    os.makedirs(persist_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=persist_dir)
    print("ChromaDB client initialized at:", persist_dir)

    print("Ingesting embeddings into ChromaDB (collection: candidates)...")
    # convert embeddings to list of lists to be JSON-serializable for Chroma
    coll = ingest_to_chroma(client, ids=ids, embeddings=embeddings.tolist(), metadatas=metadatas, documents=documents)
    print("Ingestion completed. Collection cardinality:", coll.count())


if __name__ == "__main__":
    main()
