from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from buttons import RequestButtons

sp = SpotifyPlayer()
kc = KeyboardController()
while True:
    reqs = kc.getRequests()
    if RequestButtons.Button1 in reqs:
        sp.play()
    if RequestButtons.Button2 in reqs:
        sp.pause()
    if RequestButtons.Button3 in reqs:
        playlist = "https://open.spotify.com/playlist/0mYyjgP25uzu2rxBplV69l"
        sp.play(link=playlist)
    

