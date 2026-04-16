"""
Populate knowledge base from various file formats.
Supports: PDF, DOCX, TXT, and legacy TOON files.
Uses batch embedding for throughput.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import glob
import uuid
import argparse
from app.database.vector_db import VectorDB
from app.ml.utils.embeddings import get_embedding, get_embeddings_batch
from app.core.cv_processor import CVProcessor


def populate_from_cvs(cv_dir: str):
    """Batch-process all CVs in a directory and store in VectorDB."""
    print(f"📂 Scanning {cv_dir} for CV files...")
    
    extensions = ["*.pdf", "*.docx", "*.txt"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(cv_dir, ext)))
    
    if not files:
        print("No CV files found.")
        return
    
    print(f"Found {len(files)} files to process.")
    
    vector_db = VectorDB()
    cv_processor = CVProcessor()
    
    all_ids = []
    all_texts = []
    all_metadatas = []
    
    for filepath in files:
        print(f"  Processing: {os.path.basename(filepath)}...")
        try:
            processed = cv_processor.process(filepath)
            text = processed["text"]
            
            if not text.strip():
                print(f"  ⚠ Skipping (empty text): {filepath}")
                continue
            
            cv_id = str(uuid.uuid4())
            all_ids.append(cv_id)
            all_texts.append(text)
            all_metadatas.append({
                "source": filepath,
                "filename": os.path.basename(filepath),
                "chunk_count": processed["metadata"]["chunk_count"]
            })
            print(f"  ✅ Parsed: {processed['metadata']['chunk_count']} chunks")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    if not all_texts:
        print("No documents to embed.")
        return
    
    # Batch embed for throughput
    print(f"\n🔢 Generating embeddings for {len(all_texts)} documents...")
    all_embeddings = get_embeddings_batch(all_texts, batch_size=32)
    
    # Store in VectorDB
    print(f"💾 Storing {len(all_ids)} documents in VectorDB...")
    vector_db.add_embeddings(
        ids=all_ids,
        embeddings=all_embeddings,
        metadatas=all_metadatas,
        documents=all_texts
    )
    
    print(f"✅ Successfully populated knowledge base with {len(all_ids)} CVs.")
    
    # Print stats
    stats = vector_db.get_stats()
    print(f"\n📊 Database Stats: {stats}")
    vector_db.close()


def populate_from_text_files(kb_dir: str):
    """Populate from plain text knowledge base files."""
    print(f"📂 Scanning {kb_dir} for text files...")
    
    txt_files = glob.glob(os.path.join(kb_dir, "*.txt"))
    
    if not txt_files:
        print("No text files found.")
        return
    
    vector_db = VectorDB()
    
    all_ids = []
    all_texts = []
    all_metadatas = []
    
    for filepath in txt_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                continue
            
            doc_id = str(uuid.uuid4())
            all_ids.append(doc_id)
            all_texts.append(content)
            all_metadatas.append({"source": os.path.basename(filepath)})
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    if all_texts:
        print(f"Generating embeddings for {len(all_texts)} documents...")
        all_embeddings = get_embeddings_batch(all_texts, batch_size=32)
        
        vector_db.add_embeddings(
            ids=all_ids,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            documents=all_texts
        )
        print(f"✅ Added {len(all_ids)} documents to knowledge base.")
    
    vector_db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate the CV-Job Matcher knowledge base.")
    parser.add_argument(
        "--source", type=str, default="data/uploads",
        help="Directory containing CV files (PDF/DOCX/TXT)"
    )
    parser.add_argument(
        "--mode", type=str, choices=["cvs", "text"], default="cvs",
        help="Mode: 'cvs' to process CV files, 'text' for plain text files"
    )
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_dir = os.path.join(base_dir, args.source)
    
    if args.mode == "cvs":
        populate_from_cvs(source_dir)
    else:
        populate_from_text_files(source_dir)
