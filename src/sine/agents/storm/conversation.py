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

            writer_question, question_msg = perspectivist.chat(
                self.topic, self.chat_history
            )
            if writer_question and not self.is_qa_ending(writer_question):
                expert_answer, answer_msg = expert.chat(self.topic, writer_question)
                if expert_answer:
                    self.chat_history.append(question_msg)
                    self.chat_history.append(answer_msg)

        # collect expert search engine results after conversation
        self.search_results.extend(expert.collected_results)

        return self.chat_history[1:]
    
    def export(self):
        '''export chat history to string'''
        
        if not self.chat_history:
            logger.warning("chat history is empty")
            return ''
        
        conversation_str = "\n"
        for i in range(1, len(self.chat_history), 2):
            Q = self.chat_history[i]
            A = self.chat_history[i+1]
            conversation_str += f"Q: {Q}\n"
            conversation_str += f"A: {A}\n"

        logger.debug(f"Formatted conversation:\n{conversation_str}")

        return conversation_str
    
    def is_qa_ending(self, response):
        ending_str = 'Thank you so much for your help!'
        lines = response.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        return ending_str in lines
