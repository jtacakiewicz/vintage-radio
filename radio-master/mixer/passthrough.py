from pyo import *
from .effect import Effect

class PassthroughEffect():
    def __init__(self, input_obj):
        super().__init__()
        input_obj.out()

    def on(self):
        pass

    def off(self):
        pass

    def setValue1(self, v: float):
        pass

    def setValue2(self, v: float):
        pass
