from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from buttons import RequestButtons

sp = SpotifyPlayer()
kc = KeyboardController()
kc.setVolumeCallback(lambda x, y: print(f"Volume: {y}", end="\r\n"))
kc.setRequestCallback(lambda req: sp.switch(req))
kc.setEffectCallback(lambda e, a: print(f"Effect: {e}-{a}", end="\r\n"))
kc.run_loop()
