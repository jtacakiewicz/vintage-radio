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

# Half-sine window used as the amplitude envelope of the overlaps.
env = WinTable(8)

# Length of the window in seconds.
wsize = 0.1

# Amount of transposition in semitones.
trans = -3

# Compute the transposition ratio.
ratio = pow(2.0, trans / 12.0)

# Compute the reading head speed.
rate = -(ratio - 1) / wsize

# Two reading heads out-of-phase.
ind = Phasor(freq=rate, phase=[0, 0.5])

# Each head reads the amplitude envelope...
win = Pointer(table=env, index=ind, mul=0.7)

# ... and modulates the delay time (scaled by the window size) of a delay line.
# mix(1) is used to mix the two overlaps on a single audio stream.
snd = Delay(inp, delay=ind * wsize, mul=win).mix(1)

stereo = snd.mix(2)
# The transposed signal is sent to the right speaker.
stereo.out()


s.start()
print("🎧 Running realtime pitch shift + reverb… Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
    s.stop()
    s.shutdown()

