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

# Sets values for 8 LFO'ed delay lines (you can add more if you want!).
# LFO frequencies.
freqs = [0.254, 0.465, 0.657, 0.879, 1.23, 1.342, 1.654, 1.879]
# Center delays in seconds.
cdelay = [0.0287, 0.0102, 0.0311, 0.01254, 0.0134, 0.01501, 0.02707, 0.0178]
# Modulation depths in seconds.
adelay = [0.001, 0.0012, 0.0013, 0.0014, 0.0015, 0.0016, 0.002, 0.0023]

# Create 8 sinusoidal LFOs with center delays "cdelay" and depths "adelay".
lfos = Sine(freqs, mul=adelay, add=cdelay)

# Create 8 modulated delay lines with a little feedback and send the signals
# to the output. Streams 1, 3, 5, 7 to the left and streams 2, 4, 6, 8 to the
# right (default behavior of the out() method).
delays = Delay(inp, lfos, feedback=0.5, mul=0.5).out()


s.start()
print("🎧 Running realtime pitch shift + reverb… Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
    s.stop()
    s.shutdown()

