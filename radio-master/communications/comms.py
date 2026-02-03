import sys
import time
import wiringpi

device = "/dev/i2c-0"
i2caddr = 0x35

def main():
    wiringpi.wiringPiSetup()
    fd = wiringpi.wiringPiI2CSetupInterface(device, i2caddr)
    
    if fd < 0: 
        print("Błąd: Nie można połączyć się z urządzeniem I2C")
        return

    def update_led(index, r, g, b):
        wiringpi.wiringPiI2CWriteReg16(fd, index, (r << 8) | 0)
        time.sleep(0.005)
        wiringpi.wiringPiI2CWriteReg16(fd, index, (g << 8) | 1)
        time.sleep(0.005)
        wiringpi.wiringPiI2CWriteReg16(fd, index, (b << 8) | 2)
        time.sleep(0.005)
        wiringpi.wiringPiI2CWriteReg16(fd, 255, 0)

    try:
        while True:
            wiringpi.wiringPiI2CWrite(fd, 0) 
            time.sleep(0.01) # Czas dla ATtiny na reakcję

            raw_data = []
            for _ in range(6):
                raw_data.append(wiringpi.wiringPiI2CRead(fd))

            p5_min = 804
            p5_max = 1023

            p4_min = 0
            p4_max = 975

            p3_min = 605
            p3_max = 935

            val_p5 = (((raw_data[0] << 8) | raw_data[1]) - p5_min) / ( p5_max - p5_min  )
            val_p4 = (((raw_data[2] << 8) | raw_data[3]) - p4_min) / ( p4_max - p4_min  )
            val_p3 = (((raw_data[4] << 8) | raw_data[5]) - p3_min) / ( p3_max - p3_min  )
            val_p5 = min( max( val_p5 , 0), 1)
            val_p4 = min( max( val_p4 , 0), 1)
            val_p3 = min( max( val_p3 , 0), 1)

            print(f"Odczyty 10-bit -> P5(A0): {val_p5:4}, P4(A2): {val_p4:4}, P3(A3): {val_p3:4}")
            
            time.sleep(0.2) # Częstotliwość odświeżania

    except KeyboardInterrupt:
        print("\nZatrzymano przez użytkownika")
        sys.exit(0)

if __name__ == '__main__':
    main()
