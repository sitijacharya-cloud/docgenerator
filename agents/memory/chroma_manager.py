import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import os


class ChromaManager:
    def __init__(self, persist_directory: str = "./storage/chromadb"):
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        self.collection = self.client.get_or_create_collection(
            name="documented_code",
            metadata={"description": "Well-documented code examples"}
        )
    
    def add_documented_component(
        self, 
        component_id: str, 
        source_code: str, 
        docstring: str, 
        metadata: dict
    ):
        """Store a documented component for future reference."""
        try:
            self.collection.add(
                documents=[source_code],
                metadatas=[{
                    "component_id": component_id,
                    "docstring": docstring,
                    **metadata
                }],
                ids=[component_id]
            )
        except Exception as e:
            print(f"Error adding to ChromaDB: {e}")
    
    def find_similar_components(
        self, 
        source_code: str, 
        n_results: int = 2
    ) -> List[Dict]:
        """Find similar documented components."""
        try:
            if self.collection.count() == 0:
                return []
            
            results = self.collection.query(
                query_texts=[source_code],
                n_results=min(n_results, self.collection.count())
            )
            
            similar = []
            if results['documents'] and results['metadatas']:
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    similar.append({
                        'source': doc,
                        'docstring': metadata.get('docstring', ''),
                        'component_id': metadata.get('component_id', '')
                    })
            
            return similar
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []
    
    def clear_collection(self):
        """Clear all data from the collection."""
        try:
            self.client.delete_collection("documented_code")
            self.collection = self.client.get_or_create_collection(
                name="documented_code",
                metadata={"description": "Well-documented code examples"}
            )
        except Exception as e:
            print(f"Error clearing ChromaDB: {e}")