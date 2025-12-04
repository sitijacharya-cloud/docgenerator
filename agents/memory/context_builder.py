from typing import List, Dict
from .chroma_manager import ChromaManager


class ContextBuilder:
    def __init__(self, chroma_manager: ChromaManager):
        self.chroma = chroma_manager
    
    def build_context_for_component(self, component: dict) -> List[Dict]:
        """Build context with similar examples for a component."""
        source_code = component.get('source_code', '')
        
        if not source_code:
            return []
        
        similar_examples = self.chroma.find_similar_components(
            source_code=source_code,
            n_results=2
        )
        
        return similar_examples