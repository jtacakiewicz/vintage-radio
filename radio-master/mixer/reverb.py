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

# Four parallel stereo comb filters. The delay times are chosen
# to be as uncorrelated as possible. Prime numbers are a good
# choice for delay lengths in samples.
comb1 = Delay(inp, delay=[0.0297, 0.0277], feedback=0.65)
comb2 = Delay(inp, delay=[0.0371, 0.0393], feedback=0.51)
comb3 = Delay(inp, delay=[0.0411, 0.0409], feedback=0.5)
comb4 = Delay(inp, delay=[0.0137, 0.0155], feedback=0.73)

combsum = inp + comb1 + comb2 + comb3 + comb4

# The sum of the original signal and the comb filters
# feeds two serial allpass filters.
all1 = Allpass(combsum, delay=[0.005, 0.00507], feedback=0.75)
all2 = Allpass(all1, delay=[0.0117, 0.0123], feedback=0.61)

# Brightness control.
lowp = Tone(all2, freq=3500, mul=0.25).out()


s.start()
print("🎧 Running ...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
    s.stop()
    s.shutdown()

