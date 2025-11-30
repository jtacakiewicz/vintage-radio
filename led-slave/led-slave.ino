#define I2C_SLAVE_ADDRESS 0x4 // 7-bit address
#include <TinyWireSlave.h>

// The default buffer size
#ifndef TWI_RX_BUFFER_SIZE
#define TWI_RX_BUFFER_SIZE (16)
#endif

uint8_t i2c_regs[] = {100u};
byte reg_position;

// Character that triggers the blink
#define TRIGGER_CHAR 'A' // ASCII 'A'

void requestEvent()
{  
    TinyWireS.send(i2c_regs[0]);
    reg_position = (reg_position+1) % sizeof(i2c_regs);
}

// Blink function using tws_delay
void blinkn(uint8_t blinks)
{
    while(blinks--)
    {
        digitalWrite(1, HIGH);
        tws_delay(100);
        digitalWrite(1, LOW);
        tws_delay(100);
    }
}

// Updated I2C receive handler
void receiveEvent(uint8_t howMany)
{
    while(TinyWireS.available()>0){
        // toggles the led everytime, when an 'a' is received
        if(TinyWireS.receive()=='a') {
          digitalWrite(1, HIGH);
          tws_delay(50);
          digitalWrite(1, LOW);
        }
    }
}

void setup()
{
    pinMode(1, OUTPUT);  // LED pin
    digitalWrite(1, LOW); // LED off (active low wiring)

    TinyWireS.begin(I2C_SLAVE_ADDRESS);
    TinyWireS.onReceive(receiveEvent);
    TinyWireS.onRequest(requestEvent);
}

void loop()
{
    // Must be called in tight loop to catch stop condition
    TinyWireS_stop_check();
}


