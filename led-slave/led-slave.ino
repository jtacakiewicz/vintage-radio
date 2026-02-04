#include <TinyWireSlave.h>
#include <FastLED.h>

#define I2C_SLAVE_ADDRESS 0x35
#define NUM_LEDS 100
#define LED_DATA_PIN 1

CRGB leds[NUM_LEDS];

#define NUM_ANALOGS 3
volatile uint8_t analogBuffer[NUM_ANALOGS * 2];
volatile byte transmit_idx = 0;

// Timer variable
unsigned long lastAnalogUpdate = 0;

void requestEvent() {
    TinyWireS.send(analogBuffer[transmit_idx]);
    transmit_idx++;
    // Reset indeksu po wysłaniu całej paczki 6 bajtów
    if (transmit_idx >= (NUM_ANALOGS * 2)) transmit_idx = 0;
}

void receiveEvent(uint8_t howMany) {
    transmit_idx = 0; 

    // wiringPiI2CWriteReg16 sends 3 bytes
    if (howMany == 3) {
        byte idx      = TinyWireS.receive();
        byte colorId  = TinyWireS.receive();
        byte val      = TinyWireS.receive();

        if (idx < NUM_LEDS) {
            if (colorId == 0) { leds[idx].r = val; }
            if (colorId == 1) { leds[idx].g = val; }
            if (colorId == 2) { leds[idx].b = val; }
        } 
        else if (idx == 255) {
            FastLED.show();
        }
    } else {
        while (TinyWireS.available()) TinyWireS.receive();
    }
}

void updateAnalog(uint8_t bufferPos, uint8_t pin) {
    analogRead(pin); // Odczyt "na pusto" dla stabilizacji multipleksera
    int val = analogRead(pin);
    
    // Rozbicie na dwa bajty (Big Endian)
    analogBuffer[bufferPos]     = (val >> 8) & 0xFF; // Starszy bajt (MSB)
    analogBuffer[bufferPos + 1] = val & 0xFF;        // Młodszy bajt (LSB)
}

void setup() {
    FastLED.addLeds<NEOPIXEL, LED_DATA_PIN>(leds, NUM_LEDS);
    FastLED.setBrightness(64);
    TinyWireS.begin(I2C_SLAVE_ADDRESS);
    TinyWireS.onReceive(receiveEvent);
    TinyWireS.onRequest(requestEvent);
}

void loop() {
    TinyWireS_stop_check();
    // Only update analogs every 50ms to keep CPU free for I2C
    if (millis() - lastAnalogUpdate > 50) {
        updateAnalog(0, 0);
        updateAnalog(2, 2);
        updateAnalog(4, 3);
        lastAnalogUpdate = millis();
    }
}
