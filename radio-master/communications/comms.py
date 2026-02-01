import sys
import time
import wiringpi

device = "/dev/i2c-0"
i2caddr = 0x35

def main():
    wiringpi.wiringPiSetup()
    fd = wiringpi.wiringPiI2CSetupInterface(device, i2caddr)
    
    if fd < 0: return

    def update_channel(index, color_id, value):
        # Pack ColorID and Value into the 16-bit data slot
        # result: [index, color_id, value]
        data = (value << 8) | color_id
        wiringpi.wiringPiI2CWriteReg16(fd, index, data)
        time.sleep(0.01) # Small gap for ATtiny

    try:
        while True:
            target_idx = 5
            r, g, b = 255, 128, 64
            
            print(f"Updating LED {target_idx}...")
            update_channel(target_idx, 0, r) # Send R
            update_channel(target_idx, 1, g) # Send G
            update_channel(target_idx, 2, b) # Send B
            
            # Send 'Show' command (Index 255)
            wiringpi.wiringPiI2CWriteReg16(fd, 255, 0)

            # Read back the Echo (4 bytes)
            wiringpi.wiringPiI2CWrite(fd, 0) # Reset pointer
            echo = [wiringpi.wiringPiI2CRead(fd) for _ in range(4)]
            
            print(f"Echo -> Index: {echo[0]}, R: {echo[1]}, G: {echo[2]}, B: {echo[3]}")
            time.sleep(2)

    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()
