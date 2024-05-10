from dataclasses import dataclass
from typing import List

from sine.common.schema import Information, SearchResult


@dataclass
class Reference:
    url: str
    content: str
    citation_id: int
    selected: bool

class CitationManager:
    '''CitationManager manages references in AriticleWriter.'''
    def __init__(self) -> None:
        self.references = []

    def add_references(self, new_references: List[Reference]):
        pass

    def remove_references(self):
        pass

    def update_citation_ids(self):
        pass
