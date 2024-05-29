import re

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
        message = [dict(role="user", content=self.gen_query_protocol.format(context=topic))]
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

    def chat_A(self, question_str, search_results=None, topic=None):
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
                question=question_str, info=collected_results_str
            ))]

        response = self.llm.chat(message)
        logger.info(f"Expert answer: \n{response}")

        return response

    def chat(self, topic, message, max_search_query=2):
        if self.mode == "Q->S->A":
            # receive Question to generate serach query, then Search,
            # and finally Answer based on search results.
            queries = self.chat_Q(message)
            search_results = self.search(queries[:max_search_query])
        elif self.mode == "T->S->A":
            # use Topic to generate search queries, then Search,
            # and finally Answer, search queies and seach results are done only once
            if not self.collected_results:
                queries = self.chat_T(topic)
                search_results = self.search(queries[:max_search_query])
            search_results = self.collected_results
        else:
            raise ValueError("Invalid mode.")

        response = self.chat_A(message, search_results)
        response_msg = dict(role="assistant", content=response)

        return response, response_msg
