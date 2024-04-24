from sine.agents.storm.prompts import (REFINE_OUTLINE, WRITE_DRAFT_OUTLINE,
                                       WRITE_SECTION)
from sine.agents.storm.utils import (clean_up_outline,
                                     limit_word_count_preserve_newline,
                                     process_table_of_contents)


class OutlineWriter:
    """Write draft outline first and then improve based on conversation and
    draft outline."""

    def __init__(self, writer_engine) -> None:
        self.llm = writer_engine

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
        # write draft first
        draft_outline = self.write_draft_outline(topic)

        # format conversation
        conversation = self._format_conversation(chat_history)
        # limit the conversation tokens as the api model has upper limit token per minute
        conversation = limit_word_count_preserve_newline(conversation, max_word_count=3500)

        # improve outline
        outline = self.refine_outline(topic, draft_outline, conversation)
        outline = clean_up_outline(outline)

        return outline

class ArticleWriter:
    '''ArticleWriter write section by section.'''

    def __init__(self, writer_engine) -> None:
        self.llm = writer_engine

    def _format_snippet(self, snippets):
        info = ''
        for n, r in enumerate(snippets):
            info += f'[{n + 1}] ' + '\n'.join([r])
            info += '\n\n'
        return info

    def write_section(self, topic, section_title, vector_db):
        """Section writer writes the content of each section based on the outline
            title and the related collected results."""

        # search for section related snippets from vector_db
        selected_snippets = vector_db.search([section_title], top_k=10)
        info = self._format_snippet(selected_snippets)

        message = [
            dict(role='user',
                 content=WRITE_SECTION.format(
                     info=info,
                     topic=topic,
                     section_title=section_title)),
        ]

        response = self.llm.chat(message)

        return response

    def write(self, topic, outline, vector_db):
        """ Write the article section by section.

        Args:
            topic (str): topic of interest
            outline (str): outline of the article, with markdown hash tags,
                            e.g. #, ## indicating section and subsections etc
            vector_db (str): search section related info from vector_db

        TODO: use concurrent.futures.ThreadPoolExecutor to make it parallel,
        but mind the rate limit of the API.
        """
        outline_tree = process_table_of_contents(outline)
        outline_tree = list(outline_tree.values())[0]

        article = []
        for section in outline_tree:
            print(f'Writing {section} ...')
            section_content = self.write_section(topic, section, vector_db)
            article.append(section_content)

        return article
