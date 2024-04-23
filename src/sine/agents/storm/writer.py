from sine.agents.storm.prompts import (REFINE_OUTLINE, WRITE_DRAFT_OUTLINE,
                                       WRITE_SECTION)
from sine.agents.storm.utils import clean_up_outline, process_table_of_contents


class OutlineWriter:
    """Write draft outline first and then improve based on conversation and
    draft outline."""

    def __init__(self, writer_engine) -> None:
        self.llm = writer_engine

    def write_draft_outline(self, topic):
        message = [
            dict(role="user", content=WRITE_DRAFT_OUTLINE.format(topic)),
        ]

        response = self.llm.chat(message)

        return clean_up_outline(response)

    def _format_conversation(self, chat_history):
        # format chat history to conversation string
        conversation = "\n"
        # TODO: format chat history to conversation string
        # for i in range(0, len(chat_history), 2):
        #     conversation += f'Wikipedia Writer: {chat_history[i]['content']}\n'
        #     conversation += f'Expert: {chat_history[i+1]['content']}\n'

        return conversation

    def refine_outline(self, topic, draft_outline, conversation):
        message = [
            dict(
                role="system",
                content=REFINE_OUTLINE.format(
                    topic=topic, conversation=conversation, dfraft_outline=draft_outline
                ),
            ),
        ]

        return self.llm.chat(message)

    def write(self, topic, chat_history):
        # write draft first
        draft_outline = self.write_draft_outline(topic)

        # format conversation
        conversation = self._format_conversation(chat_history)

        # improve outline
        outline = self.refine_outline(topic, draft_outline, conversation)
        outline = clean_up_outline(outline)

        return outline

class ArticleWriter:
    '''ArticleWriter write section by section.'''

    def __init__(self, writer_engine) -> None:
        self.llm = writer_engine

    def write_section(self, topic, section_title, context_content):
        """Section writer writes the content of each section based on the outline
            title and the related collected results."""
        message = [
            dict(role='user',
                 content=WRITE_SECTION.format(
                     info=context_content,
                     topic=topic,
                     section_title=section_title)),
        ]

        response = self.llm.chat(message)

        return response

    def write(self, topic, outline, conext_content):
        """ Write the article section by section.

        Args:
            topic (str): topic of interest
            outline (str): outline of the article, with markdown hash tags,
                            e.g. #, ## indicating section and subsections etc
            context_content (str): one string about the related content collected from internet

        TODO: use concurrent.futures.ThreadPoolExecutor to make it parallel,
        but mind the rate limit of the API.
        """
        outline_tree = process_table_of_contents(outline)
        outline_tree = list(outline_tree.values())[0]

        article = []
        for section in outline_tree:
            section_content = self.write_section(topic, section, conext_content)
            article.append(section_content)

        return article
