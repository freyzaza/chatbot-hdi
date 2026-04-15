import numpy as np
import pickle
import os

class VectorDB:
    DB_FOLDER = "vectordb_storage"
    DB_FILE = os.path.join(DB_FOLDER, "vectordb.pkl")

    def __init__(self):
        self.texts = []
        self.embeddings = []

    def add(self, text, embedding):
        self.texts.append(text)
        self.embeddings.append(embedding)

    def search(self, query_embedding, top_k=5):

        sims = []

        for emb in self.embeddings:
            sim = np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb)
            )
            sims.append(sim)

        top_indices = np.argsort(sims)[-top_k:][::-1]

        return [self.texts[i] for i in top_indices]
    
    def save(self):
        """Simpan vectordb ke pickle file"""
        if not os.path.exists(self.DB_FOLDER):
            os.makedirs(self.DB_FOLDER)
        
        with open(self.DB_FILE, 'wb') as f:
            pickle.dump({
                'texts': self.texts,
                'embeddings': self.embeddings
            }, f)
        print(f"VectorDB disimpan di: {self.DB_FILE}")
    
    def load(self):
        """Muat vectordb dari pickle file"""
        if os.path.exists(self.DB_FILE):
            with open(self.DB_FILE, 'rb') as f:
                data = pickle.load(f)
                self.texts = data['texts']
                self.embeddings = data['embeddings']
            print(f"VectorDB dimuat dari: {self.DB_FILE}")
            return True
        return False