import copy
import time
from abc import ABC, abstractmethod

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

    def __init__(self, writer_llm) -> None:
        super().__init__(writer_llm)

    def write_draft_outline(self, topic):
        message = [
            dict(role="user", content=WRITE_DRAFT_OUTLINE.format(topic=topic)),
        ]

        response = self.llm.chat(message)

        return clean_up_outline(response)

    def _format_conversation(self, conversation_history):
        # format chat history to conversation string
        conversation_str = "\n"

        for conversations in conversation_history.values():
            for turn in conversations:
                if turn["role"] == "user":
                    conversation_str += f"Wikipedia writer: {turn['content']}\n"
                else:
                    conversation_str += f"Expert: {turn['content']}\n"

        return conversation_str

    def refine_outline(self, topic, draft_outline, conversation):
        message = [
            dict(
                role="user",
                content=REFINE_OUTLINE.format(
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

        article_outline = Article.create_from_outline_string(topic, outline_str)

        return article_outline

class ArticleWriter(Writer):
    '''ArticleWriter write section by section.'''

    def __init__(self, writer_llm) -> None:
        super().__init__(writer_llm)
        self.citation_manager = CitationManager()

    def _format_snippet(self, snippets):
        info = ''
        for n, r in enumerate(snippets):
            info += f'[{n + 1}] ' + '\n'.join([r])
            info += '\n\n'
        return info

    def write_section(self, topic, section_title, section_retrievals, sub_section_outline = None):
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

        message = [
            dict(role='user',
                 content=WRITE_SECTION.format(
                     info=section_retrievals,
                     topic=topic,
                     section_title=section_title)),
        ]

        response = self.llm.chat(message)

        return response

    def write(self, topic: str, article_outline: Article, retriever) -> Article:
        """ Write the article section by section.

        Args:
            topic     : topic of interest
            outline   : outline of the article, with markdown hash tags,
                            e.g. #, ## indicating section and subsections etc
            retriever : search section related info from retriever

        TODO: use concurrent.futures.ThreadPoolExecutor to make it parallel,
        but mind the rate limit of the API.
        TODO: retriever abstraction
        """
        final_article = copy.deepcopy(article_outline)
        final_article.remove_subsection_nodes()
        sections_to_write = final_article.get_sections()
        for section_node in sections_to_write:
            logger.info(f"Writing section: {section_node.section_name}")
            # article_outline's subsections are used for retrieval
            section_node_outline = article_outline.find_section(section_node.section_name)
            section_queries = section_node_outline.get_children_names(include_self = True)
            retrievals = retriever.search(section_queries, top_k = 10)


            section_content = self.write_section(topic, section_node.section_name, retrievals)
            section_content_node = ArticleNode.create_from_markdown(section_content)


            section_node.add_child(section_content_node)

            time.sleep(10) # hack to avoid api model rate limit

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
