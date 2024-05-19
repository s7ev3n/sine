from typing import Type

from sine.agents.storm.expert import Expert
from sine.agents.storm.perspectivist import Perspectivist
from sine.common.logger import logger


class Conversation:
    def __init__(self, topic, max_turn=4):
        self.topic = topic
        self.max_turn = max_turn
        self.chat_history = []
        self.search_results = []

    def start_conversation(
        self, perspectivist: Type[Perspectivist], expert: Type[Expert]
    ):
        # simulate multi-turn conversation between perspectivist and expert
        for i in range(self.max_turn):
            logger.info(f"Start the {i+1} conversation between perspectivist and expert.")
            # perspectivist ask question
            writer_question, question_msg = perspectivist.chat(
                self.topic, self.chat_history
            )
            
            # expert answer question
            expert_answer, answer_msg = expert.chat(self.topic, writer_question)
            if expert_answer:
                self.chat_history.append(question_msg)
                self.chat_history.append(answer_msg)

        self.search_results.extend(expert.collected_results)

        return self.chat_history
