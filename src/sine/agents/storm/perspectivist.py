"""Perspectivist explore given topic."""

import re

from sine.agents.storm.prompts import (ASK_QUESTION,
                                       DEFAULT_WRITER_PERSPECTIVE,
                                       FIND_RELATED_TOPIC,
                                       GENERATE_WRITERS_PERSPECTIVE)
from sine.agents.storm.utils import get_wiki_page_title_and_toc
from sine.common.logger import logger
from sine.common.utils import is_valid_url


class PerspectiveGenerator:
    """PerspectiveGen generates perspectives for the given topic, each
    perspective foucses on important aspects of the given topic."""

    def __init__(self, llm, topic):
        self.llm = llm
        self.topic = topic

    def find_related_topics(self):
        message = [
            dict(role="user", content=FIND_RELATED_TOPIC.format(topic=self.topic)),
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

    def generate(self, max_perspective=5):
        # find related topics (wiki pages), return urls are wiki links
        urls = self.find_related_topics()

        # extract content
        info = self.extract_title_and_toc(urls)
        info = "\n".join(info)

        # generate perspectives
        perspectives = [DEFAULT_WRITER_PERSPECTIVE]
        perspectives.extend(self._generate_perspectives(info)[:max_perspective])

        logger.info(f"Generated {len(perspectives)} perspectives: {perspectives}")

        return perspectives

    def _generate_perspectives(self, info):
        message = [
            dict(role="user", content=GENERATE_WRITERS_PERSPECTIVE.format(info=info)),
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

    def __init__(self, perspectivist_engine, perspective):
        self.llm = perspectivist_engine
        self._perspective = perspective

    @property
    def perspective(self):
        return self._perspective

    def chat(self, topic, chat_history):
        if len(chat_history) == 0:
            chat_history.append(
                dict(
                    role="user",
                    content=ASK_QUESTION.format(topic=topic, persona=self.perspective),
                )
            )
        try:
            response = self.llm.chat(chat_history)
            logger.info(f"Perspectivist ({self._perspective}) ask: {response}")
        except BaseException:
            logger.warning("Perspectivist failed.")
            response = ""

        response_msg = dict(role="assistant", content=response)

        return response, response_msg
