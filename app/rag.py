import json
import os
import math
import uuid
import ollama
from typing import List, Dict, Any

DB_FILE = "rag_db.json"

class RAGEngine:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.db = self._load_db()

    def _load_db(self) -> Dict[str, Any]:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_db(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.db, f)

    def _get_embedding(self, text: str, model: str) -> List[float]:
        try:
            # Ensure model is pulled or available. 
            # If this fails, we return empty list.
            response = ollama.embeddings(model=model, prompt=text)
            return response.get('embedding', [])
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        # Basic check for dimension mismatch
        if len(v1) != len(v2):
            return 0.0
            
        dot_product = sum(a*b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a*a for a in v1))
        magnitude2 = math.sqrt(sum(b*b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def add_document(self, session_id: str, text: str, filename: str, model_name: str = "llama3"):
        """
        Chunk text, get embeddings, and store in JSON.
        """
        # 1. Chunking
        chunk_size = 500  
        overlap = 50
        chunks = []
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if len(chunk) < 50: continue 
            chunks.append(chunk)
            
        if not chunks:
            return

        if session_id not in self.db:
            self.db[session_id] = []

        # 2. Process chunks
        for chunk in chunks:
            embedding = self._get_embedding(chunk, model_name)
            if embedding:
                self.db[session_id].append({
                    "id": str(uuid.uuid4()),
                    "text": chunk,
                    "filename": filename,
                    "embedding": embedding,
                    "model": model_name # Store model used
                })
        
        self._save_db()

    def query(self, session_id: str, query_text: str, model_name: str = "llama3", n_results: int = 3) -> str:
        """
        Find most relevant chunks using cosine similarity.
        """
        if session_id not in self.db or not self.db[session_id]:
            return ""

        # 1. Get query embedding
        query_embedding = self._get_embedding(query_text, model_name)
        
        if not query_embedding:
            return ""

        # 2. Calculate similarities
        scored_chunks = []
        for item in self.db[session_id]:
            # Only compare if models match (or dimensions match)
            # Ideally we should re-embed if models differ, but that's slow.
            # For now, we just try. _cosine_similarity handles dim mismatch.
            score = self._cosine_similarity(query_embedding, item['embedding'])
            scored_chunks.append((score, item['text']))

        # 3. Sort and retrieve
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        top_chunks = [chunk for score, chunk in scored_chunks[:n_results] if score > 0.2] # Threshold
        
        return "\n\n".join(top_chunks)

    def clear_session(self, session_id: str):
        if session_id in self.db:
            del self.db[session_id]
            self._save_db()

rag_engine = RAGEngine()
