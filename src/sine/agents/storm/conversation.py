from typing import Type

from sine.agents.storm.expert import Expert
from sine.agents.storm.perspectivist import Perspectivist


class Conversation:
    def __init__(self, topic, max_turn=4):
        self.topic = topic
        self.max_turn = max_turn
        self.chat_history = []

    def log(self):
        """Save the conversation history to the log file."""
        # TODO: log the conversation history

    def start_conversation(
        self, perspectivist: Type[Perspectivist], expert: Type[Expert]
    ):
        # simulate multi-turn conversation between perspectivist and expert
        for _ in range(self.max_turn):
            # perspectivist ask question
            writer_question, question_msg = perspectivist.chat(
                self.topic, self.chat_history
            )
            self.chat_history.append(question_msg)

            # expert answer question
            expert_answer, answer_msg = expert.chat(self.topic, writer_question)
            self.chat_history.append(answer_msg)

        return self.chat_history
