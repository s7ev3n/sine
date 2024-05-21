import re
from typing import Dict

from sine.actions.google_search import GoogleSearch
from sine.agents.storm.prompts import ANSWER_QUESTION, GEN_SEARCH_QUERY
from sine.common.logger import logger


class Expert:
    def __init__(self, 
                 expert_engine, 
                 search_engine, 
                 gen_query_protocol,
                 answer_question_protocol,
                 mode="T->S->A"):
        self.llm = expert_engine
        self.search_engine = search_engine
        self.gen_query_protocol = gen_query_protocol
        self.answer_question_protocol = answer_question_protocol
        self.mode = mode
        self.collected_results = []

    def chat_Q(self, question_str):
        message = [dict(role="user",
                        content=self.gen_query_protocol.format(question=question_str))]

        response = self.llm.chat(message)
        matches = re.findall(r'- "(.*)"', response)
        queries = [match.strip() for match in matches]

        logger.info(f"Expert generated search queries based on '{question_str}':\n{queries}")

        return queries

    def chat_T(self, topic):
        # generate search queries base on topic
        message = [dict(role="user", content=self.gen_query_protocol.format(topic=topic))]
        try:
            response = self.llm.chat(message)
            logger.info(f"Expert generated search queries based on {topic}:\n{response}")
        except BaseException:
            logger.warning("Failed to generate search queries.")
            response = ""

        matches = re.findall(r'- "(.*)"', response)
        queries = [match.strip() for match in matches]

        return queries

    def search(self, queries, top_k: int = 5):
        # search the internet
        for q in queries:
            tool_return = self.search_engine.run(q, top_k)
            self.collected_results.extend(tool_return.result)
        logger.debug(f"Expert search results of '[{queries}]': {self.collected_results}")
        return self.collected_results

    def chat_A(self, question_str, search_results=None):
        # answer based on search results snippets
        collected_results_str = ''
        if search_results:
            for result in self.collected_results:
                collected_results_str += '\n'
                collected_results_str += result.to_string()
        else:
            logger.warning("No search results, directly answer question")

        message= [dict(
            role="user",
            content=self.answer_question_protocol.format(
                question=question_str, context=collected_results_str
            ))]

        response = self.llm.chat(message)
        logger.info(f"Expert answer: \n{response}")

        return response

    def chat(self, topic, message, max_search_query=1):
        if self.mode == "Q->S->A":
            # receive Question to generate serach query, then Search, 
            # and finally Answer based on search results.
            queries = self.chat_Q(message)
        elif self.mode == "T->S->A":
            # use Topic to generate search queries, then Search, and finally Answer
            queries = self.chat_T(topic)
        else:
            raise ValueError("Invalid mode.")
        
        # if no queries parsed, direct QA
        if not queries:
            logger.critical("No search queries")
            response = self.chat_A(message)
            return response, dict(role="assistant", content=response)

        search_results = self.search(queries[:max_search_query])
        response = self.chat_A(message, search_results)
        response_msg = dict(role="assistant", content=response)

        return response, response_msg

class ExpertOld:
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
            collected_results_str += result.snippets_string()

        return dict(
            role="user",
            content=ANSWER_QUESTION.format(
                topic=topic, info=collected_results_str
            ),
        )

    def search_queries(self, queries, top_k: int = 5):
        """google search for the internet."""

        for query in queries:
            try:
                tool_return = self.search_engine.run(query, top_k)
                self.collected_results.extend(tool_return.result)
            except BaseException:
                logger.warning(f"Failed to search [{query}] from the internet.")
                continue

        return self.collected_results

    def collect_from_internet(self, topic, top_k: int = 5):
        """Search the internet for the topic, and return internet results."""
        # expand the search queries from the topic
        message = [dict(role="user", content=GEN_SEARCH_QUERY.format(topic=topic))]
        try:
            response = self.llm.chat(message)
            logger.info(f"Expert generated search queries based on {topic}:\n{response}")
        except BaseException:
            logger.warning("Failed to generate search queries.")
            response = ""

        matches = re.findall(r'- "(.*)"', response)
        queries = [match.strip() for match in matches]
        results = self.search_queries(queries)

        return self.collected_results

    def chat(self, topic, question_str):
        if not len(self.collected_results):
            logger.info("Expert collecting from internet using search engine...")
            self.collect_from_internet(topic=topic)

        if self.default_message is None:
            self.default_message = self._default_prompt(topic, self.collected_results)

        messages = [self.default_message]
        messages.append(dict(role="assistant", content="Qusetion: " + question_str))
        try:
            response = self.llm.chat(messages)
            logger.info(f"Expert answer: {response}")
        except BaseException:
            logger.warning("Expert failed to chat.")


        response_msg = dict(role="assistant", content=response)

        return response, response_msg
