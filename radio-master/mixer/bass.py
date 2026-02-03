from pyo import *
from .effect import Effect

class BassBoostEffect(Effect):
    def __init__(self, input_source):
        # Input
        self.internal_input = InputFader(input_source)

        # Params
        self.freq = Sig(150)      # cutoff Hz
        self.boost_db = Sig(10)   # boost in dB

        # ON/OFF smooth
        self.fader = SigTo(value=0, time=0.05)

        # === Bass extraction ===
        self.low = ButLP(self.internal_input, freq=self.freq)

        # dB -> linear gain
        self.boost_gain = Pow(10, self.boost_db / 20.0)

        # boosted bass
        self.boosted_low = self.low * self.boost_gain

        # bass + original
        self.bass_boost_mix = self.internal_input + self.boosted_low

        # compressor (anti-clipping)
        self.cmp = Compress(self.bass_boost_mix, thresh=-12, ratio=3)

        # crossfade dry/wet
        self.mix = Interp(self.internal_input, self.cmp, self.fader)

        self._output = self.mix

    @property
    def output(self):
        return self._output

    def setInput(self, inp):
        if inp is None:
            return
        self.internal_input.setInput(inp)

    def on(self):
        self.fader.value = 1.0

    def off(self):
        self.fader.value = 0.0

    def setValue1(self, v: float):
        """Bass freq: 60–250 Hz"""
        self.freq.value = 60 + (v * 190)

    def setValue2(self, v: float):
        """Boost: 0–20 dB"""
        self.boost_db.value = v * 20

