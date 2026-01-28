from pyo import *
import time
import math
from .effect import Effect

class FlangerEffect(Effect):
    def __init__(self, input_source):
        self.internal_input = InputFader(input_source)
        self.middelay = 0.005
        self.depth = Sig(0.99)
        self.lfospeed = Sig(0.3)
        self.feedback = Sig(0.3, mul=0.95)
        # Smooth toggling (0 = off, 1 = on)
        self.fader = SigTo(value=0, time=0.05)
        # LFO: Controls delay time
        self.lfo = Sine(freq=self.lfospeed, mul=self.middelay * self.depth, add=self.middelay)
        # Flanger Core
        # DCBlock is good practice inside the Delay loop for stability
        self.flg = Delay(self.internal_input, delay=self.lfo, feedback=self.feedback)
        # Compression and Output
        # We apply the fader here to enable/disable the effect's contribution
        self.cmp = Compress(self.internal_input + self.flg, thresh=-20, ratio=4, mul=self.fader)

    @property
    def output(self):
        return self.cmp

    def setInput(self, inp):
        if inp is None:
            return
        self.internal_input.setInput(inp)

    def on(self):
        self.fader.value = 1

    def off(self):
        self.fader.value = 0

    def setValue1(self, v: float):
        """Sets LFO Speed (Hertz)"""
        self.lfospeed.value = v

    def setValue2(self, v: float):
        """Sets Feedback (0 to 1)"""
        # We keep the 0.95 safety multiplier from your original code
        self.feedback.value = v * 0.95

# middelay = 0.005                            # seconds
#
# depth = Sig(0.99)                           # 0 --> 1
# lfospeed = Sig(0.3)                         # Hertz
# feedback = Sig(0.3, mul=0.95)               # 0 --> 1
#
# # LFO with adjusted output range to control the delay time in seconds.
# lfo = Sine(freq=lfospeed, mul=middelay * depth, add=middelay)
#
# # Dynamically delayed signal. The source passes through a DCBlock
# # to ensure there is no DC offset in the signal (with feedback, DC
# # offset can be fatal!).
# flg = Delay(inp, delay=lfo, feedback=feedback)
#
# # Mix the original source with its delayed version.
# # Compress the mix to normalize the output signal.
# cmp = Compress(inp + flg, thresh=-20, ratio=4).out()
#
# s.start()
# print("🎧 Running realtime pitch shift + reverb… Press Ctrl+C to stop.")
#
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     print("\nStopping...")
#     s.stop()
#     s.shutdown()
#
#
