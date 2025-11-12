from spotify_player import SpotifyPlayer
import time

sp = SpotifyPlayer()
sp.next()
print(sp.progress())
