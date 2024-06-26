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
                 preference,
                 draft_outline_protocol,
                 refine_outline_protocol) -> None:
        super().__init__(writer_llm)
        self.topic = topic
        self.preference = preference
        self.draft_outline_protocol = draft_outline_protocol
        self.refine_outline_protocol = refine_outline_protocol

    def write_draft_outline(self):
        message_str = self.draft_outline_protocol.format(topic=self.topic, preference=self.preference)
        response = self._gen(message_str)

        return clean_up_outline(response)

    def refine_outline(self, draft_outline, conversations):
        message_str = self.refine_outline_protocol.format(
                    preference=self.preference,
                    topic=self.topic,
                    conversation=''.join(conversations),
                    draft_outline=draft_outline
                )

        return self._gen(message_str)

    def write(self, conversations):
        # TODO: Important! write a good outline is vital ! It is the skelton of the whole
        # article, it guides all the section generation steps.
        # Currently, conversation history is used for refining outline. The question are
        # a) How to verify that the conversation actually improve the final outline ?
        # b) What metric do we use to evaluate the quality of the outline ?
        # c) Could user preference be used as one of the outline evalution metrics ?
        # d) Could we use chats of user and Expert to improve the outline ?
        #    This could reflect user perference but users do not know what they do not know.

        # step 1: write draft first
        draft_outline = self.write_draft_outline()
        logger.info(f"Draft outline (directly generated by llm):\n {draft_outline}")

        # step 2: using converations to refine the directly generated outline
        outline_str = self.refine_outline(draft_outline, conversations)
        outline_str = clean_up_outline(outline_str)
        logger.info(f"Refined outline (improved by conversation):\n {outline_str}")

        article_outline = Article.create_from_markdown(self.topic, outline_str)

        return article_outline

class ArticleWriter(Writer):
    '''ArticleWriter write section by section.'''

    def __init__(self,
                 writer_llm,
                 topic,
                 preference,
                 write_section_protocol = None,
                 write_subsection_protocol = None,
                 write_style_protocol = None) -> None:
        super().__init__(writer_llm)
        self.topic = topic
        self.preference = preference
        self.write_section_protocol = write_section_protocol
        self.write_subsection_protocol = write_subsection_protocol
        self.write_style_protocol = write_style_protocol
        self.citation_manager = CitationManager()

    @property
    def writer_system_prompt(self):
        assert self.write_style_protocol is not None, "write_style_protocol is not defined"
        return dict(role='system', content=self.write_style_protocol)

    def _gen_subsection(self, title, info, prev_content):
        assert self.write_subsection_protocol is not None, "write_subsection_protocol is not defined"
        message_str = self.write_subsection_protocol.format(
            info=info,
            topic=self.topic,
            section_title=title,
            prev_content=prev_content)

        messages = [self.writer_system_prompt, dict(role='user', content=message_str)]
        return self._gen(messages)

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
            if node.level == 2:
                logger.info(f"Start: {'#' * node.level} {node.section_name}")
            if node.level > 2:
                title = node.section_name
                logger.info(f"Writing: {'#' * node.level} {title}")
                retrievals = retriever.query(node.section_name)
                retrievals_cid = self.citation_manager.get_citation_string(retrievals)

                content = self._gen_subsection(title, retrievals_cid, prev_content)
                # gen subsection often has title as the first line, remove it
                content = _process_content(title, content)
                # TODO: remove duplicated citation, as webpage chunks now may be from the same article
                content = self.citation_manager.update_section_content_cite_id(content, retrievals)
                node.content = content

            # HACK: to avoid api model rate limit
            time.sleep(15)

            # Recursively handle children if there are any
            for child_node in node.children:
                child_content_node = _write_recursive(child_node, retriever, prev_content)
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

def _process_content(pattern, text):
    parts = text.split(f"{pattern}", 1)
    if len(parts) > 1:
        return parts[1].strip()
    else:
        return text

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
