from abc import ABC, abstractmethod

class Effect(ABC):
    """An abstract base class representing a sound effect."""

    def __init__(self, input_obj):
        pass

    @abstractmethod
    def on(self):
        pass

    @abstractmethod
    def off(self):
        pass

    @abstractmethod
    def setValue1(self, v: float):
        pass

    @abstractmethod
    def setValue2(self, v: float):
        pass
