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

last_vol = 0
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
def setRequest(req):
    print(f"Request made: {req}", end="\r\n")
    sp.switch(req)

def setEffectValue(v1, v2):
    mx.setValue1(v1)
    mx.setValue2(v2)

def setVolume(vol):
    global last_vol
    last_vol = vol
    pulse.volume_set_all_chans(sink, vol)

kc.setVolumeCallback(setVolume)
kc.setRequestCallback(setRequest)
kc.setEffectCallback(setEffect)
kc.setOptionalValueCallback(setEffectValue)
try:
    while True:
        kc.update()
        kc.setStrip1(last_vol, 255, 255, 255)
        kc.setStrip2(last_vol, 255, 255, 255)
        wiringpi.delay(1) 
except KeyboardInterrupt:
    print("\nZamykanie kontrolera...")
