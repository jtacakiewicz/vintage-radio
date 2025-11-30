#define I2C_SLAVE_ADDRESS 0x4 // 7-bit address
#define LED_BUILTIN 1
#include <TinyWireSlave.h>

#include <Arduino.h>
#include <FastLED.h>


#define NUM_LEDS 20
#define LED_DATA_PIN 3

CRGB leds[NUM_LEDS];
unsigned long last_time;
bool isFlushed = true;

#define FLUSH_IDX 255
#define UNFLUSHED_DATA 0
#define FLUSHED_DATA 1 

//returns 1 if data is up to date or 0 if it is not
void requestEvent()
{  
    TinyWireS.send((byte)isFlushed);
}


// data structure:
// led index, (if 255 will flush, but still expects r, g, b)
// r,
// g,
// b
void receiveEvent(uint8_t howMany)
{
    if(howMany != 4) {
        while(TinyWireS.available()>0){
            TinyWireS.receive();
        }
        return;
    }
    byte idx = TinyWireS.available();
    byte r = TinyWireS.available();
    byte g = TinyWireS.available();
    byte b = TinyWireS.available();
    if(idx < NUM_LEDS) {
        isFlushed = false;
        leds[idx] = CRGB(r, g, b);
    }
    if(idx == FLUSH_IDX) {
        isFlushed = true;
        FastLED.show();
    }

    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
}

void setup()
{
    last_time = millis();
    pinMode(LED_BUILTIN, OUTPUT);  // LED pin
    digitalWrite(LED_BUILTIN, LOW); // LED off (active low wiring)
    FastLED.addLeds<NEOPIXEL, LED_DATA_PIN>(leds, NUM_LEDS);  // GRB ordering is assumed

    TinyWireS.begin(I2C_SLAVE_ADDRESS);
    TinyWireS.onReceive(receiveEvent);
    TinyWireS.onRequest(requestEvent);
}

bool blank = false;
void loop()
{
    if(millis() - last_time > 500) {
        if(blank) {
            leds[0] = CRGB::Red;
            FastLED.show();
        }else {
            leds[0] = CRGB::Black;
            FastLED.show();
        }
        blank = !blank;
        last_time = millis();
    }
    TinyWireS_stop_check();
}


// #ifndef TWI_RX_BUFFER_SIZE
// #define TWI_RX_BUFFER_SIZE (16)
// #endif
