"""STORM pipeline."""

from dataclasses import dataclass

from sine.agents.storm.conversation import Conversation
from sine.agents.storm.expert import Expert
from sine.agents.storm.perspectivist import PerspectiveGenerator, Perspectivist
from sine.agents.storm.writer import ArticleWriter, OutlineWriter
from sine.models.api_model import APIModel


@dataclass
class STORMConfig:
    topic: str
    max_perspectivist: int = 8
    max_conversation_turn: int = 4
    conversation_llm: str = "llama3-8b-8192"
    question_asker_llm: str = "llama3-8b-8192"
    outline_llm: str = "llama3-70b-8192"
    article_llm: str = "llama3-70b-8192"


class STORM:
    def __init__(self, cfg: STORMConfig) -> None:
        self.cfg = cfg

    def init(self):
        self._init_llms()
        self._init_topic_explorer()

    def _init_topic_explorer(self):
        self.topic_explorer = PerspectiveGenerator(self.conversation_llm, self.cfg.topic)

    def _init_llms(self):
        self.conversation_llm = APIModel(self.cfg.conversation_llm)
        self.question_asker_llm = APIModel(self.cfg.question_asker_llm)
        self.outline_llm = APIModel(self.cfg.outline_llm)
        self.article_llm = APIModel(self.cfg.article_llm)

    def _init_conversation_roles(self):
        perspectives = self.topic_explorer.generate(max_perspective=self.cfg.max_perspectivist)
        perspectivists = [Perspectivist(self.conversation_llm, perspective) for perspective in perspectives]
        expert = Expert(self.conversation_llm)

        return perspectivists, expert

    def _init_writers(self):
        self.outline_writer = OutlineWriter(self.outline_llm)
        self.article_writer = ArticleWriter(self.article_llm)

    def run_conversations(self):
        # TODO: make conversations run in parallel threads to speed up
        perspectivists, expert = self._init_conversation_roles()
        conversations = {}
        for perspectivist in perspectivists:
            conversation = Conversation(self.cfg.topic, self.cfg.max_conversation_turn)
            chat_history = conversation.start_conversation(perspectivist, expert)

            conversations[perspectivist.perspective] = chat_history

    def run_storm(self):
        # step 1: let us explore the topics from different perspectives and
        # gather the information through each perspective and expert (equiped
        # with search tools) conversation
        conversation_history = self.run_conversations()

        # step 2: let us generate the outline based on the conversation history
        outline = self.outline_writer.write(self.cfg.topic, conversation_history)

        # step 3: let us write the article section by section
        article = self.article_writer.write(self.cfg.topic, outline, conversation_history)

        # step 4: post process the article
        # TODO: post process citations and polish

        return article
