import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SentenceTransformerSearch:
    '''Navie embeder and retrieval model using sentence transformer.'''
    def __init__(self):
        self.encoder = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    def encoding(self, snippets):
        self.snippets = snippets
        self.encoded_snippets = self.encoder.encode(snippets, show_progress_bar=True)

    def search(self, queries, top_k: int = 5):
        assert self.encoded_snippets is not None, "Please encode the snippets first by calling the encoding method."

        selected_snippets = []
        if type(queries) is str:
            queries = [queries]

        for query in queries:
            encoded_query = self.encoder.encode(query, show_progress_bar=False)
            sim = cosine_similarity([encoded_query], self.encoded_snippets)[0]
            sorted_indices = np.argsort(sim)
            for i in sorted_indices[-top_k:][::-1]:
                selected_snippets.append(self.snippets[i])

        return selected_snippets
