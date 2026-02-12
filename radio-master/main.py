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
import time
import pulsectl
import wiringpi

device = "/dev/i2c-0"
i2caddr = 0x35
LED_MODE_VOLUME = 0
LED_MODE_EFFECT = 1
effect_timeout_ms = 5000

led_mode = LED_MODE_VOLUME
last_effect_change = 0

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
    global led_mode, last_effect_change

    now = int(time.time() * 1000)

    led_mode = LED_MODE_EFFECT
    last_effect_change = now

    kc.setStrip1(v1, 0, 255, 0)
    kc.setStrip2(v2, 0, 0, 255)
    mx.setValue1(v1)
    mx.setValue2(v2)

def setVolume(vol):
    global led_mode, last_vol
    pulse.volume_set_all_chans(sink, vol)

    led_mode = LED_MODE_VOLUME
    kc.setStrip1(vol, 127, 127, 127)
    kc.setStrip2(vol, 127, 127, 127)
    last_vol = vol

kc.setVolumeCallback(setVolume)
kc.setRequestCallback(setRequest)
kc.setEffectCallback(setEffect)
kc.setOptionalValueCallback(setEffectValue)
try:
    while True:
        kc.update()

        now = int(time.time() * 1000)
        if led_mode == LED_MODE_EFFECT:
            if (now - last_effect_change) > effect_timeout_ms:
                led_mode = LED_MODE_VOLUME
                kc.setStrip1(last_vol, 127, 127, 127)
                kc.setStrip2(last_vol, 127, 127, 127)

        kc.flushStrips()
        wiringpi.delay(1)
except KeyboardInterrupt:
    print("\nZamykanie kontrolera...")
