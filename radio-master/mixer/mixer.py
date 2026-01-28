from typing import Type
from .effect import Effect
from buttons import EffectButtons

class Mixer:
    def __init__(self, use_pyo=True):
        if use_pyo:
            from pyo import Server, Input
            RATE = 44100
            CHANNELS = 2
            CHUNK = 16384
            INPUT_DEVICE = 11
            OUTPUT_DEVICE = 11
            self.s = Server(sr=RATE, nchnls=CHANNELS, buffersize=CHUNK, duplex=1).boot()
            self.s.setInputDevice(INPUT_DEVICE)
            self.s.setOutputDevice('hw:1,0')
            self.s.boot()
            self.input = Input(chnl=[0, 1])
            self.s.start()
        else:
            self.input = None
            self.s = None

        self.effects = {}
        print("Mixer running . . .", end="\r\n")

    def addEffect(self, new_effect: Type[Effect], effect_type: EffectButtons):
        self.effects[effect_type] = new_effect(self.input)
        self.effects[effect_type].off()

    def on(self, effect_type: EffectButtons):
        if effect_type in self.effects:
            self.effects[effect_type].on()

    def off(self, effect_type: EffectButtons):
        if effect_type in self.effects:
            self.effects[effect_type].off()

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
