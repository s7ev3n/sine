import re
from dataclasses import dataclass
from typing import Dict, List, Type

from sine.agents.storm.retriever import SearchEngineResult, Source
from sine.common.logger import logger


@dataclass
class Reference:
    url: str
    title: str
    content: str
    cite_id: int = None

class CitationTable:
    '''CitationTable manages references in AriticleWriter.'''
    def __init__(self) -> None:
        self.references = []

    def add_new_reference(self, new_info: Type[Source]):
        cite_id = len(self.references) + 1
        new_reference = self.to_reference(new_info, cite_id)
        self.references.append(new_reference)

        return cite_id

    def to_citation_markdown(self):
        reference_str = '## References'
        for ref in self.references:
            reference_str += f'\n\n[{ref.cite_id}]. {ref.title}. {ref.url}.\n\n'

        return reference_str

    def to_reference(self, search_result: Type[SearchEngineResult], cite_id: int):
        ref = Reference(
            url=search_result.url,
            title=search_result.title,
            content=search_result.to_string(),
            cite_id=cite_id
        )
        return ref

    def __len__(self):
        return len(self.references)

class CitationManager:
    '''CitationManger manage CitationTable.'''

    def __init__(self) -> None:
        self.article_references = CitationTable()

    def get_citation_string(self, retrievals: List[Source]):
        citation_string = ''
        for n, r in enumerate(retrievals):
            citation_string += f'[{n + 1}] ' + '\n'.join([r.to_string()])
            citation_string += '\n'

        return citation_string

    def get_cite_id_from_section_content(self, section_content):
        cite_ids = {int(x) for x in re.findall(r'\[(\d+)\]', section_content)}
        return cite_ids

    def update_section_content_cite_id(self, section_content, retrievals):
        """Update section content (which has section cite ids) with article cite ids.

        Args:
            section_content (str): the generated section content using section retrievals which has section level cite ids
            retrievals (List[SearchResult]): the retrievals used to generate the section content, some of them are cited by SectionWriter, but some of them are not, we update article reference table the cited

        Return:
            section_content (str): the updated section content with article level cite ids
        """
        section2article_cite_id_mapping = {}
        section_cite_ids = self.get_cite_id_from_section_content(section_content)

        if not len(section_cite_ids):
            logger.debug("No citation id found in the section content.")
            return section_content

        for cite_id in section_cite_ids:
            if cite_id < 1 or cite_id > len(retrievals):
                logger.debug(f"cite id `{cite_id}` is invalid")
                continue
            article_cite_id = self.article_references.add_new_reference(retrievals[cite_id - 1])
            section2article_cite_id_mapping[cite_id] = article_cite_id

        updated_section_content = self._update_to_article_citation(section_content, section2article_cite_id_mapping)

        return updated_section_content

    def _update_to_article_citation(self, section_content, cite_id_mapping: Dict):
        for section_cite_id in cite_id_mapping.keys():
            section_content = section_content.replace(f"[{section_cite_id}]", f"__PLACEHOLDER_{section_cite_id}__")

        for section_cite_id, article_cite_id in cite_id_mapping.items():
            section_content = section_content.replace(f"__PLACEHOLDER_{section_cite_id}__", f"[{article_cite_id}]")

        return section_content

    def get_article_reference_section(self):
        """Return the article reference section (level 2 in article) in markdown format."""
        return self.article_references.to_citation_markdown()
