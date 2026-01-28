from typing import Type
from .effect import Effect
from buttons import EffectButtons

class Mixer:
    def __init__(self, use_pyo=True):
        if use_pyo:
            from pyo import Server, Input, InputFader, pa_list_devices
            pa_list_devices()

            RATE = 44100
            CHANNELS = 2
            CHUNK = 16384
            self.s = Server(sr=RATE, nchnls=CHANNELS, buffersize=CHUNK, duplex=1)
            self.s.setInputDevice(11)
            self.s.setOutputDevice(11)
            self.s.boot()
            self.input = Input(chnl=[0, 1])
            self.master = InputFader(self.input)
            self.master.out()
            self.s.start()
            import time
            time.sleep(1.0)
        else:
            self.input = None
            self.s = None

        self.effects = {}
        self.active_order = []
        print("Mixer running", end="\r\n")

    def addEffect(self, new_effect: Type[Effect], effect_type: EffectButtons):
        self.effects[effect_type] = new_effect(self.input)
        self.effects[effect_type].off()

    def _repatch(self):
        """The core logic: reconnects the chain based on activation order."""
        current_source = self.input
        for effect in self.active_order:
            effect.setInput(current_source)
            current_source = effect.output
        self.master.setInput(current_source)

    def on(self, effect_type: EffectButtons):
        if effect_type in self.effects:
            instance = self.effects[effect_type]
            instance.on()
            self.active_order.append(instance)
            self._repatch()

    def off(self, effect_type: EffectButtons):
        if effect_type in self.effects:
            instance = self.effects[effect_type]
            instance.off()
            self.active_order.remove(instance)
            self._repatch()

    def setValue1(self, effect_type: EffectButtons, v: float):
        if effect_type in self.effects:
            self.effects[effect_type].setValue1(v)

    def setValue2(self, effect_type: EffectButtons, v: float):
        if effect_type in self.effects:
            self.effects[effect_type].setValue2(v)

    def __del__(self):
        if self.s:
            self.s.stop()
            self.s.shutdown()
