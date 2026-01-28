from pyo import *

RATE = 44100
CHANNELS = 2
CHUNK = 16384
INPUT_DEVICE = 11
OUTPUT_DEVICE = 11

s = Server(sr=RATE, nchnls=CHANNELS, buffersize=CHUNK, duplex=1)
s.setInputDevice(INPUT_DEVICE)
s.setOutputDevice(OUTPUT_DEVICE)
s.boot()

# Stereo input (channels 0 and 1)
keep_alive = Sine(freq=5, mul=0.01).out()
inp = Input(chnl=[0, 1])

# Send input directly to speakers
inp.out()

s.start()

print("🎧 Passthrough running. Press Ctrl+C to stop.")

try:
    while True:
        pass
except KeyboardInterrupt:
    s.stop()
    time.sleep(0.2)
    s.shutdown()

