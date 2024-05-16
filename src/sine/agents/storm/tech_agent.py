"""Writing tech article agent."""
import time

from sine.actions.google_search import GoogleSearch
from sine.agents.storm.article import Article
from sine.agents.storm.conversation import Conversation
from sine.agents.storm.expert import TechExpert
from sine.agents.storm.perspectivist import Perspectivist
from sine.agents.storm.prompts_tech import (ANSWER_QUESTION,
                                            GEN_SEARCH_QUERY_ON_QUESION,
                                            PREDEFINED_PERSPECTIVES)
from sine.agents.storm.sentence_transformer_retriever import (
    SearchResult, SentenceTransformerRetriever)
from sine.agents.storm.storm_agent import STORMConfig, STORMStatus
from sine.agents.storm.writer import ArticleWriter, OutlineWriter
from sine.common.logger import logger
from sine.models.api_model import APIModel


class TechStorm:
    def __init__(self, cfg: STORMConfig) -> None:
        self.cfg = cfg
        self.state = STORMStatus.STANDBY
        self.final_article = Article(self.cfg.topic)
        log_str = f"TechSTORM config:\ntopic: {self.cfg.topic}\nmax_perspectivist: {self.cfg.max_perspectivist}" + \
                f"\nmax_conversation_turn: {self.cfg.max_conversation_turn}" + \
                f"\nconversation_llm:{self.cfg.conversation_llm}" + \
                f"\noutline_llm: {self.cfg.outline_llm}" + \
                f"\narticle_llm: {self.cfg.article_llm}"
        logger.info(log_str)

    def init(self):
        self.conversation_llm = APIModel(self.cfg.conversation_llm)
        self.outline_llm = APIModel(self.cfg.outline_llm)
        self.article_llm = APIModel(self.cfg.article_llm)
        logger.info('initialized llms')

        self.outline_writer = OutlineWriter(self.outline_llm)
        self.article_writer = ArticleWriter(self.article_llm)
        logger.info('initialized writers')

        self.retriever = SentenceTransformerRetriever()

    def _init_conversation_roles(self):
        perspectives = PREDEFINED_PERSPECTIVES
        perspectivists = [Perspectivist(self.conversation_llm, perspective) for perspective in perspectives]
        protocols = dict(
            search_query_from_question=GEN_SEARCH_QUERY_ON_QUESION,
            answer_question=ANSWER_QUESTION
        )
        expert = TechExpert(self.conversation_llm, GoogleSearch(), protocols, "Q->S->A")
        logger.info(f'initialized {len(perspectivists)} editor agents and expert agent')

        return perspectivists, expert

    def run_conversations(self):
        perspectivists, expert = self._init_conversation_roles()

        # expert retrieve knowledge (currently from google search)
        # search_results is List[SearchResult]
        search_results = []
        conversations = {}
        for perspectivist in perspectivists:
            conversation = Conversation(self.cfg.topic, self.cfg.max_conversation_turn)
            chat_history = conversation.start_conversation(perspectivist, expert)
            conversations[perspectivist.perspective] = chat_history
            search_results.extend(conversation.search_results)
            time.sleep(10) # hack to avoid api model rate limit

        return conversations, search_results

    def run_pipeline(self):
        pass
