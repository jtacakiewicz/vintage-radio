from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from controller.wiring_controller import WiringController
from mixer.mixer import Mixer
from mixer.harmony import HarmonizerEffect
from mixer.flanger import FlangerEffect
from mixer.chorus import ChorusEffect
from mixer.reverb import ReverbEffect
from mixer.bass import BassBoostEffect
from buttons import EffectButtons
import pulsectl
import wiringpi

device = "/dev/i2c-0"
i2caddr = 0x35

sp = SpotifyPlayer()

pulse = pulsectl.Pulse('volume-controller')
sink = pulse.sink_list()[0]

kc = WiringController()
fd = wiringpi.wiringPiI2CSetupInterface(device, i2caddr)

mx = Mixer()
mx.addEffect(HarmonizerEffect, effect_type=EffectButtons.Voice)
mx.addEffect(ReverbEffect, effect_type=EffectButtons.Jazz)
mx.addEffect(FlangerEffect, effect_type=EffectButtons.Spatial3D)
mx.addEffect(BassBoostEffect, effect_type=EffectButtons.Bass)
mx.addEffect(ChorusEffect, effect_type=EffectButtons.Orchestra)

def setEffect(e, active):
    print(f"Setting effect of {e} to {active}", end="\r\n")
    if active:
        mx.on(e)
    else:
        mx.off(e)
def setEffectValue(v1, v2):
    print(f"Values: {v1}, {v2}", end="\r\n")
    mx.setValue1(v1)
    mx.setValue2(v2)

kc.setVolumeCallback(lambda _, vol: pulse.volume_set_all_chans(sink, vol))
kc.setRequestCallback(lambda req: sp.switch(req))
kc.setEffectCallback(setEffect)
kc.setOptionalValueCallback(setEffectValue)
# kc.run_loop()
try:
    while True:
        wiringpi.wiringPiI2CWrite(fd, 0) 
        wiringpi.delay(1)

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
        mx.setValue1(val_p5)
        mx.setValue2(val_p3)
        pulse.volume_set_all_chans(sink, val_p4)

        kc.update()
        wiringpi.delay(1)

except KeyboardInterrupt:
    print("Exiting controller", end="\r\n")
