from abc import ABC, abstractmethod
from buttons import Buttons

class MusicPlayer(ABC):
    """An abstract base class representing a music player."""

    def __init__(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def previous(self):
        pass

    @abstractmethod
    def switch(self, button: Buttons):
        pass

    @abstractmethod
    def progress(self)-> float:
        pass

    @abstractmethod
    def seek(self, time: float):
        pass


