import logging
import re

from sine.actions.google_search import GoogleSearch
from sine.agents.storm.prompts import ANSWER_QUESTION, GEN_SEARCH_QUERY
from sine.common.schema import ActionStatusCode


class Expert:
    """Expert use search tools for internet content, and answer perspectivist
    question."""

    def __init__(self, expert_engine):
        self.llm = expert_engine
        self.search_engine = GoogleSearch()
        self.collected_results = []
        self.default_message = None

    def _default_prompt(self, topic, collected_results):
        collected_results_str = ''
        for result in collected_results:
            collected_results_str += '\n'
            collected_results_str += result

        return dict(
            role="system",
            content=ANSWER_QUESTION.format(
                topic=topic, info=collected_results_str
            ),
        )

    def _search(self, query, top_k: int = 5):
        """Generate related questions and google search for the internet."""
        return self.search_engine.run(query, top_k)

    def collect_from_internet(self, topic, top_k: int = 5):
        """Search the internet for the topic, and return internet results."""
        # expand the search queries from the topic
        message = [dict(role="user", content=GEN_SEARCH_QUERY.format(topic=topic))]
        response = self.llm.chat(message)
        matches = re.findall(r'- "(.*)"', response)
        queries = [match.strip() for match in matches]

        for query in queries:
            tool_return = self._search(query, top_k)
            self.collected_results.extend(tool_return.result)

        return self.collected_results

    def chat(self, topic, question_str):
        if not len(self.collected_results):
            logging.info("Collecting from internet using search engine...")
            self.collect_from_internet(topic=topic)

        if self.default_message is None:
            self.default_message = self._default_prompt(topic, self.collected_results)

        messages = [self.default_message]
        messages.append(dict(role="assistant", content="Qusetion: " + question_str))

        response = self.llm.chat(messages)
        response_msg = dict(role="assistant", content=response)

        return response, response_msg
