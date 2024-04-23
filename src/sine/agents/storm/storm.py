"""STORM pipeline."""

from sine.agents.storm.conversation import Conversation
from sine.agents.storm.expert import Expert
from sine.agents.storm.perspectivist import PerspectiveGenerator, Perspectivist


class STORM:
    def __init__(self, topic) -> None:
        self.topic = topic

    def init_multi_agents(self):
        pass

    def run_storm(self):
        pass

    def run_conversations(self):
        pass
