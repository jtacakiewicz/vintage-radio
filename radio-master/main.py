from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from buttons import RequestButtons

sp = SpotifyPlayer()
kc = KeyboardController()
while True:
    reqs = kc.getRequests()
    for r in reqs:
        sp.switch(r)
