from abc import ABC, abstractmethod
from typing import Set
from buttons import RequestButtons
from buttons import EffectButtons

class IOController(ABC):
    """An abstract base class representing an IO processor."""

    def __init__(self):
        pass

    @abstractmethod
    def getRequests(self)->Set[RequestButtons]:
        pass

    @abstractmethod
    def getEffects(self)->Set[EffectButtons]:
        pass
