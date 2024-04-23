from sine.agents.storm.prompts import REFINE_OUTLINE, WRITE_DRAFT_OUTLINE
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


class SectionWriter:
    """Section writer writes the content of each section based on the outline
    title and the related collected results in previous step."""

    def __init__(self, writer_engine) -> None:
        self.llm = writer_engine

    def write_section(self, section_title):
        pass

    def retrieval(self, section_title):
        pass
