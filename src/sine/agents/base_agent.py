'''from https://github.com/InternLM/lagent/blob/main/lagent/agents/base_agent.py'''

class BaseAgent:
    """Base agent of all agents.
    
    Args:
        model (LLM): The LLM model service
        action_executor: manage all actions and their response.
        protocol: manage agent's prompt, parses response into ReAct format.
    """

    def __init__(self, model, action_executor, protocol):
        self._model = model
        self._action_executor = action_executor
        self._protocol = protocol

    def add_action(self, action) -> None:
        """Add an action to the action manager.

        Args:
            action (BaseAction): the action to be added.
        """
        self._action_executor.add_action(action)

    def del_action(self, name: str) -> None:
        """Delete an action from the action manager.

        Args:
            name (str): the name of the action to be deleted.
        """
        self._action_executor.del_action(name)

    def chat(self, message: str, **kwargs):
        raise NotImplementedError

