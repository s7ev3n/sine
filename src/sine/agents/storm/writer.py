import copy
import time
from abc import ABC, abstractmethod
from typing import List
from sine.agents.storm.article import Article, ArticleNode
from sine.agents.storm.citation import CitationManager
from sine.agents.storm.prompts import (POLISH_PAGE, REFINE_OUTLINE,
                                       WRITE_DRAFT_OUTLINE, WRITE_LEAD_SECTION,
                                       WRITE_SECTION)
from sine.agents.storm.utils import (clean_up_outline,
                                     limit_word_count_preserve_newline)
from sine.common.logger import logger


class Writer(ABC):
    def __init__(self, writer_llm) -> None:
        self.llm = writer_llm

    @abstractmethod
    def write(self, *args, **kwargs) -> Article:
        """Each writer implement its own write prompts."""


class OutlineWriter(Writer):
    """Write draft outline first and then improve based on conversation and
    draft outline."""

    def __init__(self, writer_llm, 
                 draft_outline_protocol,
                 refine_outline_protocol) -> None:
        super().__init__(writer_llm)
        self.draft_outline_protocol = draft_outline_protocol
        self.refine_outline_protocol = refine_outline_protocol

    def write_draft_outline(self, topic):
        message = [
            dict(role="user", content=self.draft_outline_protocol.format(topic=topic)),
        ]

        response = self.llm.chat(message)

        return clean_up_outline(response)

    def _format_conversation(self, conversation_history):
        # format chat history to conversation string
        conversation_str = "\n"

        for conversations in conversation_history.values():
            for turn in conversations:
                if turn["role"] == "user":
                    conversation_str += f"Writer: {turn['content']}\n"
                else:
                    conversation_str += f"Expert: {turn['content']}\n"

        return conversation_str

    def refine_outline(self, topic, draft_outline, conversation):
        message = [
            dict(
                role="user",
                content=self.refine_outline_protocol.format(
                    topic=topic, conversation=conversation, draft_outline=draft_outline
                ),
            ),
        ]

        return self.llm.chat(message)

    def write(self, topic, chat_history):
        # step 1: write draft first
        draft_outline = self.write_draft_outline(topic)
        logger.info(f"Draft outline (directly generated by llm):\n {draft_outline}")

        # step 2: using converations to refine the directly generated outline
        # format conversation
        conversation = self._format_conversation(chat_history)
        # limit the conversation tokens as the api model has upper limit token per minute
        conversation = limit_word_count_preserve_newline(conversation, max_word_count=3500)

        # improve outline
        outline_str = self.refine_outline(topic, draft_outline, conversation)
        outline_str = clean_up_outline(outline_str)
        logger.info(f"Refined outline (improved by conversation):\n {outline_str}")

        article_outline = Article.create_from_markdown(topic, outline_str)

        return article_outline

class ArticleWriter(Writer):
    '''ArticleWriter write section by section.'''

    def __init__(self, writer_llm, write_section_protocol) -> None:
        super().__init__(writer_llm)
        self.write_section_protocol = write_section_protocol
        self.citation_manager = CitationManager()

    def _generate_section(self, topic, title, info, prev):
        message = [
            dict(role='user',
                 content=self.write_section_protocol.format(
                        info=info,
                        topic=topic,
                        section_title=title.section_name)),
        ]
         
        response = self.llm.chat(message)
    
        return response

    def write_sections_recursive(self, topic, section_node, prev_content=None):
        """Section writer writes the content of each section based on retrievals and section outline.

        NOTE: The section writer only writes the first level sections, subsections' titles are used for
        retrieving information from search results, and the subsections generated are not following
        strictly the generated outline in previous steps. But you could customized to generate following
        subsection outlines.
        See the issue for detail reason: `https://github.com/stanford-oval/storm/issues/30`

        Args:
            topic (str): the topic of this article
            section_retrievals (List[SearchResult]): the information retrieved from the subsection titles using vector search
            sub_section_outline (str): the subsection outline string in markdown format (e.g. ##subtitles)

        """
        
        title = section_node.section_name 
        logger.info(f"Writing: {'#' * section_node.level} {title}")
        retrievals = self.retriever.query(section_node.section_name)
        retrievals_cid = self.citation_manager.get_citation_string(retrievals)

        content = self._generate_section(topic, title, retrievals_cid, prev_content)
        content = self.citation_manager.update_section_content_cite_id(content, retrievals)
        section_node = ArticleNode.create_from_markdown(content)
        
        # Recursively handle children if there are any
        for child_node in section_node.children:
            child_content_node = self.write_section(topic, child_node, section_node.to_string())
            section_node.add_child(child_content_node)
        
        return section_node

    def set_retriever(self, retriever):
        self.retriever = retriever

    def write(self, 
              topic: str, 
              article_outline: Article, 
              stick_article_outline=False) -> Article:
        """ Write the article section by section.

        Args:
            topic     : topic of interest
            outline   : outline of the article, with markdown hash tags,
                        e.g. #, ## indicating section and subsections etc
            sources   : list of information for retreiver
            stick_article_outline : By default, only generate section level, 
                                outline of subsections are used to retrieve
                                information from previous search results

        TODO: use concurrent.futures.ThreadPoolExecutor to make it parallel,
        but mind the rate limit of the API.
        """
        final_article = copy.deepcopy(article_outline)
        final_article.remove_section_nodes()

        for section_node in article_outline.get_sections():
            if section_node.section_name == "Introduction" or \
                section_node.section_name == "Conclusion":
                continue
            
            if stick_article_outline:
                section_content_node = self.write_sections_recursive(topic, section_node)
            else:
                logger.info(f"Writing: {'#' * section_node.level} {section_node.section_name}")
                # article_outline's subsections are used for retrieval
                section_queries = section_node.get_children_names(include_self = True)
                retrievals = self.retriever.query(section_queries, top_k_per_query=5)
                retrievals_cid = self.citation_manager.get_citation_string(retrievals)
                content = self._generate_section(topic, section_node.section_name, retrievals_cid)
                content = self.citation_manager.update_section_content_cite_id(content, retrievals)
                section_node = ArticleNode.create_from_markdown(content)
            
            final_article.article_title_node.add_child(section_content_node)
            time.sleep(10) # hack to avoid api model rate limit

        # add references
        reference_section_node = ArticleNode.create_from_markdown(self.citation_manager.get_article_reference_section())
        final_article.article_title_node.add_child(reference_section_node)

        return final_article

class LeadSectionWriter(Writer):
    """Write lead section which is the summary of the whole article.
    Lead section should be at the very top the article, even before introduction.
    """

    def __init__(self, writer_llm) -> None:
        super().__init__(writer_llm)

    def write(self, draft_article: Article):
        message = [
            dict(role="user",
                 content=WRITE_LEAD_SECTION.format(topic=draft_article.topic,
                                                   draft_article=draft_article.to_string())),
        ]

        response = self.llm.chat(message)

        return response

class ArticlePolishWriter(Writer):
    """Article polishing is removing duplicated paragraph."""

    def __init__(self, writer_llm) -> None:
        super().__init__(writer_llm)

    def write(self, draft_article: Article):

        message = [
            dict(role="user",
                 content=POLISH_PAGE.format(draft_article=draft_article.string())),
        ]

        response = self.llm.chat(message)

        return response
