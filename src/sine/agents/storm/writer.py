import copy
import time
from abc import ABC, abstractmethod

from sine.agents.storm.article import Article, ArticleNode
from sine.agents.storm.citation import CitationManager
from sine.agents.storm.prompts import POLISH_PAGE, WRITE_LEAD_SECTION
from sine.agents.storm.utils import (clean_up_outline,
                                     limit_word_count_preserve_newline)
from sine.common.logger import logger


class Writer(ABC):
    def __init__(self, writer_llm) -> None:
        self.llm = writer_llm

    def _gen(self, message_str):
        logger.debug(message_str)
        response = self.llm.chat(message_str)
        logger.debug(response)
        return response

    @abstractmethod
    def write(self, *args, **kwargs) -> Article:
        """Each writer implement its own write prompts."""


class OutlineWriter(Writer):
    """Write draft outline first and then improve based on conversation and
    draft outline."""

    def __init__(self,
                 writer_llm,
                 topic,
                 draft_outline_protocol,
                 refine_outline_protocol) -> None:
        super().__init__(writer_llm)
        self.topic = topic
        self.draft_outline_protocol = draft_outline_protocol
        self.refine_outline_protocol = refine_outline_protocol

    def write_draft_outline(self):
        message_str = self.draft_outline_protocol.format(topic=self.topic)
        response = self._gen(message_str)

        return clean_up_outline(response)

    def _format_conversation(self, conversation_history):
        # TODO: this formatting is noisy
        conversation_str = "\n"

        for conversations in conversation_history.values():
            for turn in conversations:
                if turn["role"] == "user":
                    conversation_str += f"Writer: {turn['content']}\n"
                else:
                    conversation_str += f"Expert: {turn['content']}\n"
        # limit the conversation tokens as the api model has upper limit token per minute
        conversation_str = limit_word_count_preserve_newline(conversation_str, max_word_count=3500)
        logger.debug(f"Formatted conversation:\n{conversation_str}")

        return conversation_str

    def refine_outline(self, draft_outline, conversation):
        message_str = self.refine_outline_protocol.format(
                    topic=self.topic,
                    conversation=conversation,
                    draft_outline=draft_outline
                )

        return self._gen(message_str)

    def write(self, chat_history):
        # step 1: write draft first
        draft_outline = self.write_draft_outline()
        logger.info(f"Draft outline (directly generated by llm):\n {draft_outline}")

        # step 2: using converations to refine the directly generated outline
        # format conversation
        conversation_str = self._format_conversation(chat_history)

        # improve outline
        outline_str = self.refine_outline(draft_outline, conversation_str)
        outline_str = clean_up_outline(outline_str)
        logger.info(f"Refined outline (improved by conversation):\n {outline_str}")

        article_outline = Article.create_from_markdown(self.topic, outline_str)

        return article_outline

class ArticleWriter(Writer):
    '''ArticleWriter write section by section.'''

    def __init__(self,
                 writer_llm,
                 topic,
                 write_section_protocol = None,
                 write_subsection_protocol = None) -> None:
        super().__init__(writer_llm)
        self.topic = topic
        self.write_section_protocol = write_section_protocol
        self.write_subsection_protocol = write_subsection_protocol
        self.citation_manager = CitationManager()

    def _gen_subsection(self, title, info, prev_content):
        assert self.write_subsection_protocol is not None, "write_subsection_protocol is not defined"
        message_str = self.write_subsection_protocol.format(
            info=info,
            topic=self.topic,
            section_title=title,
            prev_content=prev_content)

        return self._gen(message_str)

    def _gen_section(self, title, info):
        assert self.write_section_protocol is not None, "write_section_protocol is not defined"
        message_str = self.write_section_protocol.format(
            topic=self.topic,
            section_title=title,
            info=info)

        return self._gen(message_str)

    def write(self,
              article_outline: Article,
              article_retriever,
              stick_article_outline: bool = False) -> Article:
        """ Write the article section by section.

        Args:
            article_outline       : type: Article, with only outline, no content
            article_retriever     : retreiver which has data encoded
            stick_article_outline : By default, only generate section level,
                                    outline of subsections are used to retrieve
                                    information from previous search results

        NOTE: The section writer only writes the first level sections, subsections' titles are used for
        retrieving information from search results, and the subsections generated are not following
        strictly the generated outline in previous steps. But you could customized to generate following
        subsection outlines.
        See the issue for detail reason: `https://github.com/stanford-oval/storm/issues/30`
        """

        def _write_recursive(node, retriever, prev_content=None):
            if node.level > 2:
                title = node.section_name
                logger.info(f"Writing: {'#' * node.level} {title}")
                retrievals = retriever.query(node.section_name)
                retrievals_cid = self.citation_manager.get_citation_string(retrievals)

                content = self._gen_subsection(title, retrievals_cid, prev_content)
                # TODO: this content contains subsection names, should be removed
                content = self.citation_manager.update_section_content_cite_id(content, retrievals)
                node.content = content

            # Recursively handle children if there are any
            for child_node in node.children:
                child_content_node = _write_recursive(child_node, prev_content)
                prev_content = child_content_node.content

            return node

        final_article = copy.deepcopy(article_outline)
        final_article.remove_section_nodes()

        for section_node in article_outline.get_sections():
            if stick_article_outline:
                section_content_node = _write_recursive(section_node, article_retriever)
            else:
                # by default generate only following the first level section title
                logger.info(f"Writing: {'#' * section_node.level} {section_node.section_name}")
                section_queries = section_node.get_children_names(include_self = True)
                retrievals = article_retriever.query(section_queries, top_k_per_query=5)
                retrievals_cid = self.citation_manager.get_citation_string(retrievals)
                content = self._generate_section(section_node.section_name, retrievals_cid)
                content = self.citation_manager.update_section_content_cite_id(content, retrievals)
                section_content_node = ArticleNode.create_from_markdown(content)

            final_article.article_title_node.add_child(section_content_node)
            # HACK: to avoid api model rate limit
            time.sleep(10)

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
