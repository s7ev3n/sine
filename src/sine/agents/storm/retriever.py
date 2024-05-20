import uuid as uuid_generator
from abc import ABC, abstractmethod
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from sine.actions.jina_web_parser import JinaWebParser
from sine.agents.storm.article import ArticleNode
from sine.agents.storm.utils import chunk_text, is_markdown
from sine.common.logger import logger


class Source(ABC):
    '''Information abstract class'''
    def __init__(self, uuid: str, meta: dict = None) -> None:
        self.uuid = uuid
        self.meta = meta

    def __eq__(self, other):
        if isinstance(other, Source):
            return self.uuid == other.uuid
        return False

    @abstractmethod
    def to_string(self):
        pass

class SearchEngineResult(Source):
    def __init__(self, title: str, url: str, snippets: List[str]) -> None:
        super().__init__(uuid=url)
        self.title = title
        self.url = url
        self.snippets = snippets

    def to_string(self) -> str:
        snippets_str = ''
        for snpt in self.snippets:
            snippets_str += snpt + '\n'

        return snippets_str

    def __repr__(self) -> str:
        return f"{self.title}\n{self.url}\n{self.to_string()}\n"

    def to_dict(self) -> dict:
        return {
            "title" : self.title,
            "url" : self.url,
            "snippets" : self.snippets
        }

    @classmethod
    def create_from_dict(cls, data: dict):
        assert "title" in data, "title is required"
        assert "url" in data, "url is required"
        assert "snippets" in data, "snippets is required"

        return cls(
            title=data["title"],
            url=data["url"],
            snippets=data["snippets"]
        )

class WebpageContentChunk(Source):
    def __init__(self, uuid: str, title: str, url: str, content_chunk: str) -> None:
        super().__init__(uuid)
        self.title = title
        self.url = url
        self.content_chunk = content_chunk

    def to_string(self):
        return self.content_chunk

    @classmethod
    def from_SearchEngineResult(cls, search_engine_result: SearchEngineResult, scraper = None):
        '''Return list of webpage content chunks'''
        content_chunks = []
        if scraper is None:
            scraper = JinaWebMarkdownScraper()

        contents = scraper(search_engine_result.url)

        for ct in contents:
            uuid = uuid_generator.uuid3(uuid_generator.NAMESPACE_URL, ct)
            chunk = cls(
                uuid=uuid,
                title = search_engine_result.title,
                url = search_engine_result.url,
                content_chunk = ct
            )
            content_chunks.append(chunk)

        return content_chunks



class JinaWebMarkdownScraper:
    def __init__(self, scraper = JinaWebParser()):
        self.scraper = scraper

    def __call__(self, url: str):
        chunks = []
        status_code, markdown = self.scraper.run(url)
        if status_code == 200:
            if is_markdown(markdown):
                markdown_node = ArticleNode.create_from_markdown(markdown)
                lv2_nodes = markdown_node.children
                for n in lv2_nodes:
                    chunks.append(n.to_string())
            else:
                logger.info("Use text chunking.")
                chunks = chunk_text(markdown)

        return chunks

class SentenceTransformerRetriever:
    '''Navie embedder and retrieval model using sentence transformer.'''
    def __init__(self):
        self.encoder = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    def encoding(self, data: List[Source]):
        datastr_list = [sr.to_string() for sr in data]
        self.embeddings = self.encoder.encode(datastr_list)
        self.data_raw = data

    def query(self, queries, top_k_per_query: int = 5):
        """Return semantic closest list of Source."""
        assert len(self.embeddings), "Please encode the text first by calling the `self.encoding`."

        retrievals = []
        if isinstance(queries, str):
            queries = [queries]

        for query in queries:
            query_embedding = self.encoder.encode(query, show_progress_bar=False)
            sim = cosine_similarity([query_embedding], self.embeddings)[0]
            sorted_indices = np.argsort(sim)
            for i in sorted_indices[-top_k_per_query:][::-1]:
                if self.data_raw[i] not in retrievals:
                    retrievals.append(self.data_raw[i])

        return retrievals
