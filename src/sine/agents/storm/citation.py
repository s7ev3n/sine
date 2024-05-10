from dataclasses import dataclass

from sine.common.schema import Information, SearchResult


@dataclass
class Reference:
    url: str
    title: str
    content: str
    cite_id: int = None

class CitationTable:
    '''CitationTable manages references in AriticleWriter.'''
    def __init__(self) -> None:
        self.init_citation_table()

    def init_citation_table(self):
        self.references = []
        self.cite_ids = []

    def add_new_reference(self, new_reference):
        self.references.append(new_reference)
        self.cite_ids.append(len(self.cite_ids)+1)

    def remove_references(self):
        pass

class CitationManager:
    '''CitationManger manage CitationTable.'''

    def __init__(self) -> None:
        self.table = CitationTable()

    def to_citation_string(self, snippets):
        snippet_citation_string = ''
        for n, snp in enumerate(snippets):
            snippet_citation_string += f'[{n + 1}] ' + '\n'.join([snp.snippets_string()])
            snippet_citation_string += '\n\n'

        return snippet_citation_string

    def get_citeid_from_content(self, content_string):
        pass

    def update_section_citation(self, section_content, retrieval_pool):
        pass
