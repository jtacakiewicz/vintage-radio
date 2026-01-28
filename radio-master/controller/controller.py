from abc import ABC, abstractmethod
from typing import Set, Tuple, Callable
from buttons import RequestButtons
from buttons import EffectButtons

class IOController(ABC):
    """An abstract base class representing an IO processor."""

    def __init__(self):
        pass

    @abstractmethod
    def setRequestCallback(self, callback: Callable[[RequestButtons], None]):
        """Set callback that will take in one argument being the new request input."""
        pass

    @abstractmethod
    def setEffectCallback(self, callback: Callable[[EffectButtons, bool], None]):
        """Set callback that will take in two arguments being the effect type and whether it was just activated or just deactivated."""
        pass

    @abstractmethod
    def setVolumeCallback(self, callback: Callable[[float, float], None]):
        """Set callback to volume change, arguments being the old volume level and new volume level."""
        pass

    @abstractmethod
    def setOptionalValueCallback(self, callback: Callable[[float, float], None]):
        """Set callback to effect value change. Arguments are the two optional values."""
        pass

    def update(self):
        pass
