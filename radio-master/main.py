from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from mixer.mixer import Mixer
from mixer.dummy import DummyEffect
from mixer.harmony import HarmonizerEffect
from buttons import EffectButtons

last_effect = None
sp = SpotifyPlayer()
kc = KeyboardController()
mx = Mixer()
mx.addEffect(HarmonizerEffect, effect_type=EffectButtons.Voice)

def setEffect(e, active):
    global last_effect
    if active:
        mx.on(e)
        last_effect = e
    else:
        mx.off(e)
def setEffectValue(v1, v2):
    global last_effect
    if last_effect:
        print(f"Values: {v1}, {v2}", end="\r\n")
        mx.setValue1(last_effect, v1)
        mx.setValue2(last_effect, v2)

kc.setVolumeCallback(lambda x, y: print(f"Volume: {y}", end="\r\n"))
kc.setRequestCallback(lambda req: sp.switch(req))
kc.setEffectCallback(setEffect)
kc.setOptionalValueCallback(setEffectValue)
kc.run_loop()
