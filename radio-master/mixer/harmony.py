from pyo import *
import time
import math
from .effect import Effect

class HarmonizerEffect(Effect):
    def __init__(self, input_source):
        # Smooth toggling
        self.fader = SigTo(value=0, time=0.05)
        self.internal_input = InputFader(input_source)
        
        # Internal Parameters
        self.env = WinTable(8) # Half-sine window
        self.wsize = Sig(0.1)  # Window size in seconds
        self.trans = Sig(-3)   # Default transposition in semitones
        
        # Logic for Pitch Shifting:
        # Ratio = 2^(semitones/12)
        self.ratio = Pow(2.0, self.trans / 12.0)
        
        # Reading head speed calculation: rate = -(ratio - 1) / wsize
        self.rate = -(self.ratio - 1) / self.wsize

        # Two reading heads out-of-phase to create overlapping "grains"
        self.ind = Phasor(freq=self.rate, phase=[0, 0.5])

        # Amplitude envelope for each head
        self.win = Pointer(table=self.env, index=self.ind, mul=0.7)

        # Modulated delay lines (The core of Granular Pitch Shifting)
        # We apply the fader here to enable/disable the effect contribution
        self.snd = Delay(self.internal_input, delay=self.ind * self.wsize, mul=self.win * self.fader).mix(1)

        # Output stage: Mixed to stereo
        self.stereo = self.snd.mix(2)

    @property
    def output(self):
        return self.stereo

    def setInput(self, inp):
        if inp is None:
            return
        self.internal_input.setInput(inp)
        print("Harmonizer input set\r")

    def on(self):
        self.fader.value = 1

    def off(self):
        self.fader.value = 0

    def setValue1(self, v: float):
        """Sets Transposition (maps 0.0 -> 1.0 to -12 -> +12 semitones)"""
        self.trans.value = (v * 24.0) - 12.0

    def setValue2(self, v: float):
        """Sets Window Size (maps 0.0 -> 1.0 to 0.01s -> 0.5s)"""
        self.wsize.value = 0.01 + (v * 0.49)

# inp = Input(chnl=[0, 1])
# # Half-sine window used as the amplitude envelope of the overlaps.
# env = WinTable(8)
# # Length of the window in seconds.
# wsize = 0.1
# # Amount of transposition in semitones.
# trans = -3
# # Compute the transposition ratio.
# ratio = pow(2.0, trans / 12.0)
# # Compute the reading head speed.
# rate = -(ratio - 1) / wsize
# # Two reading heads out-of-phase.
# ind = Phasor(freq=rate, phase=[0, 0.5])
# # Each head reads the amplitude envelope...
# win = Pointer(table=env, index=ind, mul=0.7)
# # ... and modulates the delay time (scaled by the window size) of a delay line.
# # mix(1) is used to mix the two overlaps on a single audio stream.
# snd = Delay(inp, delay=ind * wsize, mul=win).mix(1)
# stereo = snd.mix(2)
# # The transposed signal is sent to the right speaker.
# stereo.out()
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
