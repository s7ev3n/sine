"""STORM pipeline."""
import time
from dataclasses import dataclass

from sine.agents.storm.conversation import Conversation
from sine.agents.storm.expert import Expert
from sine.agents.storm.perspectivist import PerspectiveGenerator, Perspectivist
from sine.agents.storm.utils import load_json, save_json
from sine.agents.storm.writer import ArticleWriter, OutlineWriter
from sine.common.logger import logger
from sine.models.api_model import APIModel
from sine.models.sentence_transformer import SentenceTransformerSearch


@dataclass
class STORMConfig:
    topic: str
    max_perspectivist: int = 8
    max_conversation_turn: int = 4
    conversation_llm: str = "llama3-8b-8192"
    question_asker_llm: str = "llama3-8b-8192"
    outline_llm: str = "llama3-70b-8192"
    article_llm: str = "llama3-70b-8192"
    saved_conversation_path: str = None
    saved_outline_path: str = None
    saved_article_path: str = None
    saved_search_results_path: str = None


class STORM:
    def __init__(self, cfg: STORMConfig) -> None:
        self.cfg = cfg

        log_str = f"STORM config:\ntopic: {self.cfg.topic}\nmax_perspectivist: {self.cfg.max_perspectivist}" + \
                f"\nmax_conversation_turn: {self.cfg.max_conversation_turn}" + \
                f"\nconversation_llm:{self.cfg.conversation_llm}" + \
                f"\nquestion_asker_llm: {self.cfg.question_asker_llm}" + \
                f"\noutline_llm: {self.cfg.outline_llm}" + \
                f"\narticle_llm: {self.cfg.article_llm}"
        logger.info(log_str)

    def init(self):
        self._init_llms()
        self._init_topic_explorer()
        self._init_writers()
        self._init_vector_search()

    def _init_topic_explorer(self):
        self.topic_explorer = PerspectiveGenerator(self.conversation_llm, self.cfg.topic)

    def _init_llms(self):
        self.conversation_llm = APIModel(self.cfg.conversation_llm)
        self.question_asker_llm = APIModel(self.cfg.question_asker_llm)
        self.outline_llm = APIModel(self.cfg.outline_llm)
        self.article_llm = APIModel(self.cfg.article_llm)
        logger.info('initialized llms')

    def _init_conversation_roles(self):
        perspectives = self.topic_explorer.generate(max_perspective=self.cfg.max_perspectivist)
        perspectivists = [Perspectivist(self.conversation_llm, perspective) for perspective in perspectives]
        expert = Expert(self.conversation_llm)
        logger.info(f'initialized {len(perspectivists)} editor agents and expert agent')

        return perspectivists, expert

    def _init_writers(self):
        self.outline_writer = OutlineWriter(self.outline_llm)
        self.article_writer = ArticleWriter(self.article_llm)
        logger.info('initialized writers')

    def _init_vector_search(self):
        self.vector_search = SentenceTransformerSearch()

    def run_conversations(self):
        # TODO: make conversations run in parallel threads to speed up
        perspectivists, expert = self._init_conversation_roles()

        # expert retrieve knowledge (currently from google search)
        retrievals = expert.collect_from_internet(self.cfg.topic)

        conversations = {}
        for perspectivist in perspectivists:
            conversation = Conversation(self.cfg.topic, self.cfg.max_conversation_turn)
            chat_history = conversation.start_conversation(perspectivist, expert)
            conversations[perspectivist.perspective] = chat_history
            time.sleep(10) # hack to avoid api model rate limit

        return conversations, retrievals


    def run_storm_pipeline(self):
        # step 1: let us explore the topics from different perspectives and
        # gather the information through each perspective and expert (equiped
        # with search tools) conversation
        if self.cfg.saved_conversation_path:
            conversation_history = load_json(self.cfg.saved_conversation_path)
            search_results = load_json(self.cfg.saved_search_results_path)
        else:
            conversation_history, search_results = self.run_conversations()
            save_json(self.cfg.saved_conversation_path, conversation_history)
            save_json(self.cfg.saved_search_results_path, search_results)

        # step 2: let us generate the outline based on the conversation history
        if self.cfg.saved_outline_path:
            with open(self.cfg.saved_outline_path) as f:
                outline = f.read()
        else:
            outline = self.outline_writer.write(self.cfg.topic, conversation_history)

        # step 3: let us write the article section by section
        self.vector_search.encoding(search_results)
        article = self.article_writer.write(self.cfg.topic, outline, self.vector_search)

        # step 4: post process the article

        return article
