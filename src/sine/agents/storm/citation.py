from dataclasses import dataclass
from typing import List 

@dataclass
class Reference:
    url: str
    content: str
    citation_id: int

class CitationManager:
    '''CitationManager manages citations in AriticleWriter.'''
    def __init__(self) -> None:
        self.references = []
    
    def add_references(self, new_references: List[Reference]):
        pass

    def remove_references(self):
        pass

    def update_citation_ids(self):
        pass