from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class Information:
    uuid: str

class SearchResult(Information):
    def __init__(self, title: str, url: str, snippets: List[str]) -> None:
        super(Information, self).__init__(uuid=url)
        self.title = title
        self.url = url
        self.snippets = snippets

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


class SentenceTransformerRetriever:
    '''Navie embedder and retrieval model using sentence transformer.'''
    def __init__(self):
        self.encoder = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    def encoding(self, search_results: List[SearchResult]):
        snippets = [sr.snippets_string() for sr in search_results]
        self.search_results = search_results
        self.embeddings = self.encoder.encode(snippets)

    def query(self, queries, top_k: int = 5):
        assert len(self.embeddings), "Please encode the text first by calling the `self.encoding`."

        retrievals = []
        if type(queries) is str:
            queries = [queries]

        for query in queries:
            query_embedding = self.encoder.encode(query, show_progress_bar=False)
            sim = cosine_similarity([query_embedding], self.embeddings)[0]
            sorted_indices = np.argsort(sim)
            for i in sorted_indices[-top_k:][::-1]:
                retrievals.append(self.search_results[i])

        return retrievals
