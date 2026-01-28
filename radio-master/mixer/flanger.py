from pyo import *
import time
import math

# Configuration
RATE = 44100
CHANNELS = 2
CHUNK = 4048*8
INPUT_DEVICE = 11
OUTPUT_DEVICE = 11

s = Server(sr=RATE, nchnls=CHANNELS, buffersize=CHUNK, duplex=1)
s.setInputDevice(INPUT_DEVICE)
s.setOutputDevice(OUTPUT_DEVICE)
s.boot()  # Must boot BEFORE creating audio objects

inp = Input(chnl=[0, 1])

# Flanger parameters                        == unit ==
middelay = 0.005                            # seconds

depth = Sig(0.99)                           # 0 --> 1
lfospeed = Sig(0.3)                         # Hertz
feedback = Sig(0.3, mul=0.95)               # 0 --> 1

# LFO with adjusted output range to control the delay time in seconds.
lfo = Sine(freq=lfospeed, mul=middelay * depth, add=middelay)

# Dynamically delayed signal. The source passes through a DCBlock
# to ensure there is no DC offset in the signal (with feedback, DC
# offset can be fatal!).
flg = Delay(inp, delay=lfo, feedback=feedback)

# Mix the original source with its delayed version.
# Compress the mix to normalize the output signal.
cmp = Compress(inp + flg, thresh=-20, ratio=4).out()

s.start()
print("🎧 Running realtime pitch shift + reverb… Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
    s.stop()
    s.shutdown()


