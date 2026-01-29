from pyo import *
import time
import math
from .effect import Effect

class ReverbEffect(Effect):
    def __init__(self, input_source):
        self.internal_input = InputFader(input_source)
        # Smooth toggling (0 = off, 1 = on)
        self.fader = SigTo(value=0, time=0.05)
        # We use Sigs for the parameters we want to control dynamically
        self.feedback_scalar = Sig(1.0) # Controls overall decay
        self.brightness = Sig(3500)     # Controls Tone frequency
        # Four parallel stereo comb filters
        # We multiply the original feedback values by our scalar
        self.comb1 = Delay(self.internal_input, delay=[0.0297, 0.0277], feedback=0.65 * self.feedback_scalar)
        self.comb2 = Delay(self.internal_input, delay=[0.0371, 0.0393], feedback=0.51 * self.feedback_scalar)
        self.comb3 = Delay(self.internal_input, delay=[0.0411, 0.0409], feedback=0.50 * self.feedback_scalar)
        self.comb4 = Delay(self.internal_input, delay=[0.0137, 0.0155], feedback=0.73 * self.feedback_scalar)

        self.combsum = self.internal_input + self.comb1 + self.comb2 + self.comb3 + self.comb4
        # Two serial allpass filters
        self.all1 = Allpass(self.combsum, delay=[0.005, 0.00507], feedback=0.75)
        self.all2 = Allpass(self.all1, delay=[0.0117, 0.0123], feedback=0.61)
        # Output stage with Brightness control and the Master Fader
        # mul=0.25 from your original script is combined with the fader
        self.out = Tone(self.all2, freq=self.brightness, mul=self.fader)

    @property
    def output(self):
        return self.out

    def setInput(self, inp):
        if inp is None:
            return
        self.internal_input.setInput(inp)

    def on(self):
        self.fader.value = 1

    def off(self):
        self.fader.value = 0

    def setValue1(self, v: float):
        """Sets Reverb Decay (maps 0.0 -> 1.0 to feedback scaling)"""
        # We cap this slightly below 1.0 to prevent infinite feedback/explosions
        self.feedback_scalar.value = v * 0.99

    def setValue2(self, v: float):
        """Sets Brightness (maps 0.0 -> 1.0 to 500Hz -> 8000Hz)"""
        self.brightness.value = 500 + (v * 7500)

# inp = Input(chnl=[0, 1])
#
# # Four parallel stereo comb filters. The delay times are chosen
# # to be as uncorrelated as possible. Prime numbers are a good
# # choice for delay lengths in samples.
# comb1 = Delay(inp, delay=[0.0297, 0.0277], feedback=0.65)
# comb2 = Delay(inp, delay=[0.0371, 0.0393], feedback=0.51)
# comb3 = Delay(inp, delay=[0.0411, 0.0409], feedback=0.5)
# comb4 = Delay(inp, delay=[0.0137, 0.0155], feedback=0.73)
#
# combsum = inp + comb1 + comb2 + comb3 + comb4
#
# # The sum of the original signal and the comb filters
# # feeds two serial allpass filters.
# all1 = Allpass(combsum, delay=[0.005, 0.00507], feedback=0.75)
# all2 = Allpass(all1, delay=[0.0117, 0.0123], feedback=0.61)
#
# # Brightness control.
# lowp = Tone(all2, freq=3500, mul=0.25).out()
#
#
# s.start()
# print("🎧 Running ...")
#
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     print("\nStopping...")
#     s.stop()
#     s.shutdown()
#
