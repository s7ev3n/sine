"""Writing tech article agent."""
import time
import os
from sine.actions.google_search import GoogleSearch
from sine.agents.storm.article import Article
from sine.agents.storm.conversation import Conversation
from sine.agents.storm.expert import Expert
from sine.agents.storm.perspectivist import Perspectivist
from sine.agents.storm.prompts_tech import (ANSWER_QUESTION,
                                            GEN_SEARCH_QUERY_ON_QUESION,
                                            PREDEFINED_PERSPECTIVES)
from sine.agents.storm.sentence_transformer_retriever import (
    SearchResult, SentenceTransformerRetriever)
from sine.agents.storm.storm_agent import STORMConfig, STORMStatus
from sine.agents.storm.writer import ArticleWriter, OutlineWriter
from sine.common.logger import logger, LOGGER_DIR
from sine.models.api_model import APIModel
from sine.common.utils import load_json, load_txt, save_json, save_txt, make_dir_if_not_exist

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
        expert = Expert(self.conversation_llm, GoogleSearch(), protocols, "Q->S->A")
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
        self.state = STORMStatus.RUNNING

        topic_str = self.cfg.topic.lower().strip().replace(' ', '_')
        storm_save_dir = os.path.join(LOGGER_DIR, topic_str)
        make_dir_if_not_exist(storm_save_dir)
        # step 1: let us explore the topics from different perspectives and
        # gather the information through each perspective and expert (equiped
        # with search tools) conversation
        conversation_history_p = os.path.join(storm_save_dir, "convsersation_history.json")
        search_results_p = os.path.join(storm_save_dir, "search_results.json")
        if os.path.exists(conversation_history_p) and os.path.exists(search_results_p):
            conversation_history = load_json(conversation_history_p)
            search_results_raw = load_json(search_results_p)
            search_results = [SearchResult.create_from_dict(sr_dict) for sr_dict in search_results_raw]
        else:
            conversation_history, search_results = self.run_conversations()
            save_json(conversation_history_p, conversation_history)
            search_results_raw = [sr.to_dict() for sr in search_results]
            save_json(search_results_p, search_results_raw)

        # step 2: let us generate the outline based on the conversation history
        outline_p = os.path.join(storm_save_dir, "outline.txt")
        if os.path.exists(outline_p):
            outline_str = load_txt(outline_p)
            outline = Article.create_from_markdown(topic=self.cfg.topic, markdown=outline_str)
        else:
            outline = self.outline_writer.write(self.cfg.topic, conversation_history)
            save_txt(outline_p, outline.to_markdown())

        # step 3: let us write the article section by section
        self.retriever.encoding(search_results)
        article = self.article_writer.write(self.cfg.topic, outline, self.retriever)

        # step 4: post process the article
        self.final_article = article.to_markdown()
        self.state = STORMStatus.STOP

        article_p = os.path.join(storm_save_dir, f"{topic_str}.txt")
        save_txt(article_p, self.final_article)
