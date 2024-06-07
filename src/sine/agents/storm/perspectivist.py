"""Perspectivist explore given topic."""

import re

from sine.agents.storm.prompts import DEFAULT_WRITER_PERSPECTIVE
from sine.agents.storm.utils import get_wiki_page_title_and_toc
from sine.common.logger import logger
from sine.common.utils import is_valid_url


class PerspectiveGenerator:
    """PerspectiveGen generates perspectives for the given topic, each
    perspective foucses on important aspects of the given topic."""

    def __init__(self, llm, gen_wiki_url_protocol, gen_perspectives_protocol):
        self.llm = llm
        self.gen_wiki_url_protocol = gen_wiki_url_protocol
        self.gen_perspectives_protocol = gen_perspectives_protocol

    def gen_wiki_url(self, topic):
        message = [
            dict(role="user", content=self.gen_wiki_url_protocol.format(topic=topic)),
        ]

        try:
            # FIXME: relying on llm generate url is not robust
            resoponse = self.llm.chat(message)
            urls = re.findall(r'https://[^\s]*', resoponse)
            if not len(urls):
                logger.critical("No related topics url parsed, please check the response.")
            urls = [url for url in urls if is_valid_url(url)]
        except BaseException:
            logger.error("Failed to find related topics.")

        logger.info(f"Find related topics urls: {urls}")

        return urls

    def extract_title_and_toc(self, urls):
        examples = []
        for url in urls:
            try:
                title, toc = get_wiki_page_title_and_toc(url)
                examples.append(f"Title: {title}\nTable of Contents: {toc}")
            except Exception as e:
                logger.warning(f"Error occurs when processing {url}: {e}")
                continue

        return examples

    def gen(self, topic, preference, max_perspective=5):
        # find related topics (wiki pages), return urls are wiki links
        urls = self.gen_wiki_url(topic)

        # extract content
        info = self.extract_title_and_toc(urls)
        info = "\n".join(info)

        # generate perspectives
        perspectives = [DEFAULT_WRITER_PERSPECTIVE]
        perspectives.extend(self.gen_perspectives(topic, preference)[:max_perspective])

        logger.info(f"Generated {len(perspectives)} perspectives: {perspectives}")

        return perspectives

    def gen_perspectives(self, topic, preference):
        message = [
            dict(role="user", content=self.gen_perspectives_protocol.format(
                topic=topic,
                preference=preference)),
        ]

        try:
            response = self.llm.chat(message)
        except BaseException:
            logger.warning("Failed to generate perspectives.")
            return []

        # process responses to obtain perspectives
        perspectives = []
        for s in response.split("\n"):
            match = re.search(r"\d+\.\s*(.*)", s)
            if match:
                perspectives.append(match.group(1))

        return perspectives


class Perspectivist:
    """Perspectivist have specific focus on the given topic and chat with
    expert."""

    def __init__(self, perspectivist_engine, perspective, ask_question_protocol):
        self.llm = perspectivist_engine
        self.ask_question_protocol = ask_question_protocol
        self._perspective = perspective

    @property
    def perspective(self):
        return self._perspective

    def chat(self, topic, chat_history):
        if len(chat_history) == 0:
            message_str = self.ask_question_protocol.format(
                topic=topic,
                persona=self.perspective
            )
            chat_history.append(dict(role="user", content=message_str))

        try:
            response = self.llm.chat(chat_history)
            logger.info(f"Perspectivist ({self._perspective}) ask: '{response}'")
        except BaseException:
            logger.warning("Perspectivist failed.")
            response = ""

        response_msg = dict(role="assistant", content=response)

        return response, response_msg
