from .effect import Effect
class DummyEffect(Effect):
    """An abstract base class representing a sound effect."""

    def __init__(self, input_obj):
        self.inp = input_obj
        print("Dummy effect initialized", end="\r\n")

    def setInput(self, inp):
        self.inp = inp
        print(f"new input to Dummy was set", end="\r\n")

    def on(self):
        print("Dummy effect is on", end="\r\n")

    def off(self):
        print("Dummy effect is off", end="\r\n")

    def setValue1(self, v: float):
        print(f"value1 set to {v}", end="\r\n")

    def setValue2(self, v: float):
        print(f"value2 set to {v}", end="\r\n")

    @property
    def output(self):
        return self.inp
