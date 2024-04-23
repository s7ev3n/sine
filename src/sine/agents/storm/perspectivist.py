"""Perspectivist explore given topic."""

import logging
import re
from typing import List

from sine.agents.storm.prompts import (ASK_QUESTION,
                                       DEFAULT_WRITER_PERSPECTIVE,
                                       FIND_RELATED_TOPIC,
                                       GENERATE_WRITERS_PERSPECTIVE)
from sine.agents.storm.utils import get_wiki_page_title_and_toc


class PerspectiveGenerator:
    """PerspectiveGen generates perspectives for the given topic, each
    perspective foucses on important aspects of the given topic."""

    def __init__(self, llm, topic):
        # TODO: add a system prompt
        self.llm = llm
        self.topic = topic

    def find_related_topics(self):
        message = [
            dict(role="user", content=FIND_RELATED_TOPIC.format(topic=self.topic)),
        ]

        related_topics = self.llm.chat(message)
        urls = [s[s.find("http") :] for s in related_topics.split("\n")][:-2]

        return related_topics, urls

    def extract_title_and_toc(self, urls):
        examples = []
        for url in urls:
            try:
                title, toc = get_wiki_page_title_and_toc(url)
                examples.append(f"Title: {title}\nTable of Contents: {toc}")
            except Exception as e:
                logging.error(f"Error occurs when processing {url}: {e}")
                continue

        return examples

    def generate(self, max_perspective=5):
        # TODO: log or save all the generate results

        # find related topics (wiki pages), return urls are wiki links
        related_topics, urls = self.find_related_topics()

        # extract content
        info = self.extract_title_and_toc(urls)

        # generate perspectives
        perspectives = [DEFAULT_WRITER_PERSPECTIVE]
        perspectives.extend(self._generate_perspectives(info)[:max_perspective])

        return perspectives

    def _generate_perspectives(self, info):
        message = [
            dict(role="user", content=GENERATE_WRITERS_PERSPECTIVE.format(info=info)),
        ]

        response = self.llm.chat(message)

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
        self.perspective = perspective

    def chat(self, topic, chat_history):
        if len(chat_history) == 0:
            chat_history.append(
                dict(
                    role="user",
                    content=ASK_QUESTION.format(topic=topic, persona=self.perspective),
                )
            )

        response = self._chat(chat_history)
        response_msg = dict(role="assistant", content=response)

        return response, response_msg

    def _chat(self, messages: List[dict]):
        return self.llm.chat(messages)
