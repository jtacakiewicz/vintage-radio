from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from mixer.mixer import Mixer
from mixer.dummy import DummyEffect
from buttons import EffectButtons

sp = SpotifyPlayer()
kc = KeyboardController()
mx = Mixer(use_pyo=False)
mx.addEffect(DummyEffect, effect_type=EffectButtons.Jazz)

kc.setVolumeCallback(lambda x, y: print(f"Volume: {y}", end="\r\n"))
kc.setRequestCallback(lambda req: sp.switch(req))
kc.setEffectCallback(lambda e, active: mx.on(e) if active else mx.off(e))
kc.run_loop()
