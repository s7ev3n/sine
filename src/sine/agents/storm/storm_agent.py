"""STORM pipeline."""
import os
import time
from dataclasses import dataclass
from enum import Enum, unique
from itertools import chain
from sine.agents.storm.article import Article
from sine.agents.storm.conversation import Conversation
from sine.agents.storm.expert import Expert
from sine.agents.storm.perspectivist import PerspectiveGenerator, Perspectivist
from sine.agents.storm.retriever import (
    SearchEngineResult, SentenceTransformerRetriever, WebPageContent)
from sine.agents.storm.utils import load_json, load_txt, save_json, save_txt
from sine.agents.storm.writer import ArticleWriter, OutlineWriter
from sine.common.logger import LOGGER_DIR, logger
from sine.common.utils import make_dir_if_not_exist
from sine.models.api_model import APIModel
from sine.actions.jina_web_parser import JinaWebParser
from sine.agents.storm.prompts import (
    GEN_WIKI_URL,
    GEN_WRITERS_PERSPECTIVE,
    ANSWER_QUESTION,
    ASK_QUESTION,
    GEN_SEARCH_QUERY,
    PREDEFINED_PERSPECTIVES,
    REFINE_OUTLINE,
    WRITE_DRAFT_OUTLINE,
    WRITE_SECTION,
    WRITE_SUBSECTION,
    WRITER_STYLE,

)

@unique
class STORMStatus(str, Enum):
    READY = 'ready'
    RUNNING = 'running'
    STOP = 'stop'

@dataclass
class STORMConfig:
    topic: str
    user_profile: str = None
    stick_generated_outline: bool = False # STORM default
    writing_sources: str = "search_snippets" # or search_webpage
    expert_mode: str = "T->S->A" # topic -> search -> answer
    expert_gen_query_protocol: str = GEN_SEARCH_QUERY
    expert_answer_question_protocol = ANSWER_QUESTION
    perspectives_generator_protocol: str = GEN_WRITERS_PERSPECTIVE
    gen_wiki_url_protocol = GEN_WIKI_URL
    perspectivist_ask_question_protocol = ASK_QUESTION
    draft_outline_protocol: str = WRITE_DRAFT_OUTLINE
    refine_outline_protocol: str = REFINE_OUTLINE
    write_section_protocol: str = WRITE_SECTION
    write_subsection_protocol: str = WRITE_SUBSECTION
    writer_style: str =WRITER_STYLE
    max_chunk_size: int = 2000
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
    hack_sleep: int = 10


class STORM:
    def __init__(self, cfg: STORMConfig) -> None:
        self.cfg = cfg
        self.state = STORMStatus.STANDBY
        self.final_article = Article(self.cfg.topic)
        log_str = f"STORM config:\ntopic: {self.cfg.topic}\nmax_perspectivist: {self.cfg.max_perspectivist}" + \
                f"\nmax_conversation_turn: {self.cfg.max_conversation_turn}" + \
                f"\nconversation_llm:{self.cfg.conversation_llm}" + \
                f"\nquestion_asker_llm: {self.cfg.question_asker_llm}" + \
                f"\noutline_llm: {self.cfg.outline_llm}" + \
                f"\narticle_llm: {self.cfg.article_llm}"
        logger.info(log_str)

    def init(self):
        self.conversation_llm = APIModel(self.cfg.conversation_llm)
        self.question_asker_llm = APIModel(self.cfg.question_asker_llm)

        self.article_llm = APIModel(self.cfg.article_llm)
        self.outline_writer = OutlineWriter(
            writer_llm=self.outline_llm,
            topic=self.cfg.topic,
            draft_outline_protocol=self.cfg.draft_outline_protocol,
            refine_outline_protocol=self.cfg.refine_outline_protocol)
        self.article_writer = ArticleWriter(
            writer_llm=self.article_llm,
            topic=self.cfg.topic,
            write_section_protocol=self.cfg.write_section_protocol,
            write_subsection_protocol=self.cfg.write_subsection_protocol,
            write_style_protocol=self.cfg.writer_style)
        logger.info('initialized llms')

        self.outline_writer = OutlineWriter(self.outline_llm)
        self.article_writer = ArticleWriter(self.article_llm)
        logger.info('initialized writers')

        self.retriever = SentenceTransformerRetriever()
        if self.cfg.perspectives_generator is not None:
            self.perspectives_generator = PerspectiveGenerator(
                self.conversation_llm, 
                gen_wiki_url_protocol=self.cfg.gen_wiki_url_protocol,
                gen_perspectives_protocol=self.cfg.perspectives_generator_protocol)
        
        self.state = STORMStatus.READY

    def _init_conversation_roles(self):
        if hasattr(self, 'perspectives_generator'):
            perspectives = self.perspectives_generator.generate(max_perspective=self.cfg.max_perspectivist)
        else:
            perspectives = PREDEFINED_PERSPECTIVES[:self.cfg.max_perspectivist]
        perspectivists = [Perspectivist(self.conversation_llm, perspective) for perspective in perspectives]
        expert = Expert(self.conversation_llm)
        logger.info(f'initialized {len(perspectivists)} editor agents and expert agent')

        return perspectivists, expert

    def run_conversations(self):
        perspectivists, expert = self._init_conversation_roles()

        # expert retrieve knowledge (currently from google search)
        # search_results is List[SearchResult]
        search_results = []
        conversations = []
        for perspectivist in perspectivists:
            conversation = Conversation(self.cfg.topic, self.cfg.max_conversation_turn)
            _ = conversation.start_conversation(perspectivist, expert)
            conversations.append(conversation.export())
            search_results.extend(conversation.search_results)
            
            time.sleep(self.cfg.hack_sleep)

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
            search_results = [SearchEngineResult.create_from_dict(sr_dict) for sr_dict in search_results_raw]
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
            outline = self.outline_writer.write(conversation_history)
            save_txt(outline_p, outline.to_markdown())

        # step 3: encode writing sources
        if self.cfg.writing_sources == 'search_webpage':
            logger.info("scraping webpage content ...")
            webpages = [WebPageContent.from_search(sr, JinaWebParser()) for sr in search_results]
            writing_sources = list(chain.from_iterable(wp.chunking(self.cfg.max_chunk_size) for wp in webpages if wp is not None))
            # writing_sources = [* wp.chunking(max_chunk_size) for wp in webpages]
        else:
            writing_sources = search_results
        # step 4: let us write the article section by section
        self.retriever.encoding(writing_sources)
        article = self.article_writer.write(outline, self.retriever, stick_article_outline=True)

        # step 4: post process the article
        self.final_article = article.to_markdown()
        self.state = STORMStatus.STOP

        article_p = os.path.join(storm_save_dir, f"{topic_str}.txt")
        save_txt(article_p, self.final_article)

        return True
