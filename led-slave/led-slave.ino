#include <TinyWireSlave.h>
#include <FastLED.h>

#define I2C_SLAVE_ADDRESS 0x35
#define NUM_LEDS 20
#define LED_DATA_PIN 3

CRGB leds[NUM_LEDS];
uint8_t echoBuffer[4] = {0, 0, 0, 0}; // [Index, R, G, B]
volatile byte transmit_idx = 0;

void requestEvent() {  
    TinyWireS.send(echoBuffer[transmit_idx]);
    transmit_idx++;
    if (transmit_idx >= 4) transmit_idx = 0;
}

void receiveEvent(uint8_t howMany) {
    transmit_idx = 0; 

    // wiringPiI2CWriteReg16 sends 3 bytes
    if (howMany == 3) {
        byte idx      = TinyWireS.receive();
        byte colorId  = TinyWireS.receive();
        byte val      = TinyWireS.receive();

        if (idx < NUM_LEDS) {
            echoBuffer[0] = idx; // Store index for echo
            
            if (colorId == 0) { leds[idx].r = val; echoBuffer[1] = val; }
            if (colorId == 1) { leds[idx].g = val; echoBuffer[2] = val; }
            if (colorId == 2) { leds[idx].b = val; echoBuffer[3] = val; }
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
}
