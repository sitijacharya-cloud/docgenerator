from abc import ABC, abstractmethod
from typing import List, Dict


class BaseParser(ABC):
    @abstractmethod
    def parse_file(self, file_path: str) -> Dict:
        """Parse a single source file."""
        pass
    
    @abstractmethod
    def extract_components(self, parsed_data: Dict) -> List[Dict]:
        """Extract code components from parsed data."""
        pass