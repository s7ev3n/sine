from abc import ABC, abstractmethod
from typing import List
import uuid as uuid_generator
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sine.common.logger import logger
from sine.agents.storm.utils import chunk_markdown, chunk_text, is_markdown
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

class WebPageContent(Source):
    def __init__(self, uuid: str, title: str, url: str, content: str) -> None:
        super().__init__(uuid)
        self.title = title
        self.url = url
        self.content = content

    def to_string(self):
        return self.content

    @classmethod
    def from_search(cls, search_engine_result: SearchEngineResult, web_scraper):
        '''Scrape web page content'''

        status_code, content = web_scraper.run(search_engine_result.url)
        if status_code == 200:
            uuid = uuid_generator.uuid3(uuid_generator.NAMESPACE_URL, content)
            return cls(
                uuid=uuid,
                title = search_engine_result.title,
                url = search_engine_result.url,
                content = content
            )

        logger.warning("web_scraper failed")
        return None
    
    def chunking(self):
        '''chunking the content, and return list of WebPageContent'''
        assert self.content is not None, "Please get webpage content first"
        chunks = []
        if is_markdown(self.content):
            chunks.extend(chunk_markdown(self.content))
        else:
            chunks.extent(chunk_text(self.content))

        chunks_webpage = []
        for c in chunks:
            uuid = uuid_generator.uuid3(uuid_generator.NAMESPACE_URL, c)
            chunks_webpage.extend(
                WebPageContent(
                    uuid=uuid,
                    title=self.title,
                    url=self.url,
                    content=c
                )
            )
        
        return chunks_webpage

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
