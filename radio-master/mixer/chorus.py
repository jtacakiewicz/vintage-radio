from pyo import *
import time
import math
from .effect import Effect

class ChorusEffect(Effect):
    def __init__(self, input_source):
        # Smooth toggling
        self.fader = SigTo(value=0, time=0.05)
        self.internal_input = InputFader(input_source)
        
        # Parameters to be controlled via interface
        self.depth_scaler = Sig(1.0)
        self.rate_scaler = Sig(1.0)

        # Original parameters from your script
        self.freqs = [0.254, 0.465, 0.657, 0.879, 1.23, 1.342, 1.654, 1.879]
        self.cdelay = [0.0287, 0.0102, 0.0311, 0.01254, 0.0134, 0.01501, 0.02707, 0.0178]
        self.adelay = [0.002, 0.0022, 0.0023, 0.0024, 0.003, 0.0026, 0.004, 0.0033]

        # Evenly spaced phases 0 → 2π
        import math
        self.phases = [i * (2 * math.pi / len(self.freqs)) for i in range(len(self.freqs))]

        # Scaled LFOs with phase offsets
        self.lfos = Sine(
            freq=[f * self.rate_scaler for f in self.freqs],
            mul=[a * self.depth_scaler for a in self.adelay],
            add=self.cdelay,
            phase=self.phases
        )

        # 8 Modulated delay lines
        # We apply the fader here to enable/disable the effect contribution
        self.out = Delay(self.internal_input, 
                            delay=self.lfos, 
                            feedback=0.5, 
                            mul=self.fader)

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
        """Sets Modulation Depth (0.0 to 2.0x original depth)"""
        self.depth_scaler.value = v * 2.0

    def setValue2(self, v: float):
        """Sets Modulation Rate (0.0 to 2.0x original speed)"""
        self.rate_scaler.value = v * 2.0

# inp = Input(chnl=[0, 1])
#
# # Sets values for 8 LFO'ed delay lines (you can add more if you want!).
# # LFO frequencies.
# freqs = [0.254, 0.465, 0.657, 0.879, 1.23, 1.342, 1.654, 1.879]
# # Center delays in seconds.
# cdelay = [0.0287, 0.0102, 0.0311, 0.01254, 0.0134, 0.01501, 0.02707, 0.0178]
# # Modulation depths in seconds.
# adelay = [0.001, 0.0012, 0.0013, 0.0014, 0.0015, 0.0016, 0.002, 0.0023]
#
# # Create 8 sinusoidal LFOs with center delays "cdelay" and depths "adelay".
# lfos = Sine(freqs, mul=adelay, add=cdelay)
#
# # Create 8 modulated delay lines with a little feedback and send the signals
# # to the output. Streams 1, 3, 5, 7 to the left and streams 2, 4, 6, 8 to the
# # right (default behavior of the out() method).
# delays = Delay(inp, lfos, feedback=0.5, mul=0.5).out()
#
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
