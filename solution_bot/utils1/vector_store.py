import chromadb
from chromadb.config import Settings
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os

class VectorStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = "./chroma_db"
        # Load existing database if it exists
        if os.path.exists(self.persist_directory):
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            self.vector_store = None
    
    def add_texts(self, texts):
        if self.vector_store is None:
            self.vector_store = Chroma.from_texts(
                texts,
                self.embeddings,
                persist_directory=self.persist_directory,
                metadata=[{"source": f"chunk_{i}"} for i in range(len(texts))]
            )
        else:
            # Add new texts to existing database
            self.vector_store.add_texts(
                texts,
                metadatas=[{"source": f"chunk_{i}"} for i in range(len(texts))]
            )
        # Persist the database
        self.vector_store.persist()
    
    def similarity_search(self, query, k=4):
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(
            query, 
            k=k,
            score_threshold=0.7  # Only return relevant matches
        )
