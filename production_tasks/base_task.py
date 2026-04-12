from abc import ABC, abstractmethod
from typing import Optional


class BaseTask(ABC):
    """
    Abstract base class for production tasks.

    This class provides a template for defining production tasks that can be
    executed in different environments such as production, local, and development.
    Subclasses must implement the `handle` method to define the specific task behavior.

    Attributes:
        envs (list of str): A list of environment names where the task can be executed.
    """

    envs = ["production", "local", "dev"]

    @abstractmethod
    def handle(self):
        raise NotImplementedError
