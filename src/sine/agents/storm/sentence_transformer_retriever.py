from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sine.actions.jina_web_parser import JinaWebParser
from sine.common.logger import logger
class Information:
    def __init__(self, uuid: str) -> None:
        self.uuid = uuid

    def __eq__(self, other):
        if isinstance(other, Information):
            return self.uuid == other.uuid
        return False

class SearchResult(Information):
    def __init__(self, title: str, url: str, snippets: List[str], content: str = None, scraper=None) -> None:
        super().__init__(uuid=url)
        self.title = title
        self.url = url
        self.snippets = snippets
        self.content = content
        self.web_scraper = scraper

    def snippets_string(self) -> str:
        snippets_str = ''
        for snpt in self.snippets:
            snippets_str += snpt + '\n'

        return snippets_str

    def __repr__(self) -> str:
        return f"{self.title}\n{self.url}\n{self.snippets_string()}\n"

    def to_dict(self) -> dict:
        return {
            "title" : self.title,
            "url" : self.url,
            "snippets" : self.snippets,
            "content" : self.content
        }

    def scrape_content(self):
        """scrape content from url to markdown string"""
        if self.web_scraper is None:
            self.web_scraper = JinaWebParser()
        
        content = None
        try:
            status_code, content = self.web_scraper(self.url)
            if status_code == 200:
                self.content = content
        except:
            logger.critical(f"Failed to scrape the content from {self.url}")

        return content
        

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


class SentenceTransformerRetriever:
    '''Navie embedder and retrieval model using sentence transformer.'''
    def __init__(self):
        self.encoder = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    def encoding(self, search_results: List[SearchResult], encode_content=False):
        if encode_content:
            logger.info("scraping content from url, it will take longer time ...")
            data = [sr.scrape_content() for sr in search_results]
        else:
            data = [sr.snippets_string() for sr in search_results]
        
        self.search_results = search_results
        self.embeddings = self.encoder.encode(data)

    def query(self, queries, top_k_per_query: int = 5):
        assert len(self.embeddings), "Please encode the text first by calling the `self.encoding`."

        retrievals = []
        if type(queries) is str:
            queries = [queries]

        for query in queries:
            query_embedding = self.encoder.encode(query, show_progress_bar=False)
            sim = cosine_similarity([query_embedding], self.embeddings)[0]
            sorted_indices = np.argsort(sim)
            for i in sorted_indices[-top_k_per_query:][::-1]:
                if self.search_results[i] not in retrievals:
                    retrievals.append(self.search_results[i])

        return retrievals
