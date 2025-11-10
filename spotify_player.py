from music_player import MusicPlayer
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyPlayer(MusicPlayer):
    def __init__(self, device_name='vintage-radio'):
        super().__init__()
        scope = "user-read-playback-state user-modify-playback-state"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        devices = self.sp.devices()
        for d in devices['devices']:
            print(d['name'], d['id'])

        self.device_id = None
        for d in devices['devices']:
            if d['name'] == device_name:
                self.device_id = d['id']
                break

    def pause(self):
        self.sp.start_playback(device_id=self.device_id)

    def play(self):
        self.sp.start_playback(device_id=self.device_id)

    def next(self):
        self.sp.next_track(device_id=self.device_id)

    def previous(self):
        self.sp.previous_track(device_id=self.device_id)

    def switch(self):
        self.sp.previous_track(device_id=self.device_id)

    def progress(self):
        info = self.sp.currently_playing()
        total_time = info['item']['duration_ms']
        cur_time = info['progress_ms']
        return cur_time / total_time

    def seek(self, time: float):
        info = self.sp.currently_playing()
        total_time = info['item']['duration_ms']
        self.sp.seek_track(int(total_time*time))


