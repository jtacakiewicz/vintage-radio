#include <TinyWireSlave.h>
#include <FastLED.h>

#define I2C_SLAVE_ADDRESS 0x35
#define NUM_LEDS 20
#define LED_DATA_PIN 1

CRGB leds[NUM_LEDS];

#define NUM_ANALOGS 3
uint8_t analogBuffer[NUM_ANALOGS] = {0, 0, 0}; // [Index, R, G, B]
volatile byte transmit_idx = 0;

void requestEvent() {  
    TinyWireS.send(analogBuffer[transmit_idx]);
    transmit_idx++;
    if (transmit_idx >= NUM_ANALOGS) transmit_idx = 0;
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

void setup() {
    FastLED.addLeds<NEOPIXEL, LED_DATA_PIN>(leds, NUM_LEDS);
    TinyWireS.begin(I2C_SLAVE_ADDRESS);
    TinyWireS.onReceive(receiveEvent);
    TinyWireS.onRequest(requestEvent);
}

void loop() {
    TinyWireS_stop_check();
    analogBuffer[0] = analogRead(0);
    analogBuffer[1] = analogRead(2);
    analogBuffer[2] = analogRead(3);
}
