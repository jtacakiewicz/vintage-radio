from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from mixer.mixer import Mixer
from mixer.harmony import HarmonizerEffect
from mixer.flanger import FlangerEffect
from mixer.chorus import ChorusEffect
from mixer.reverb import ReverbEffect
from buttons import EffectButtons
import pulsectl

sp = SpotifyPlayer()

pulse = pulsectl.Pulse('volume-controller')
sink = pulse.sink_list()[0]

kc = KeyboardController()
mx = Mixer()
mx.addEffect(HarmonizerEffect, effect_type=EffectButtons.Voice)
mx.addEffect(ReverbEffect, effect_type=EffectButtons.Jazz)
mx.addEffect(FlangerEffect, effect_type=EffectButtons.Bass)
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
kc.run_loop()
