SKETCH = led-slave
BOARD  = digistump:avr:digispark-tiny

BUILD_DIR = $(SKETCH)/build/
HEX_FILE = $(BUILD_DIR)/digistump.avr.digispark-tiny/led-slave.ino.hex

all: compile

compile:
	arduino-cli compile $(SKETCH) -b $(BOARD) -e

lib:
	arduino-cli lib install "FastLED@3.1.0"
	ARDUINO_LIBRARY_ENABLE_UNSAFE_INSTALL=true arduino-cli lib install --git-url https://github.com/sudar/TinyWire.git

upload:
	sudo micronucleus $(HEX_FILE)

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all compile upload clean

