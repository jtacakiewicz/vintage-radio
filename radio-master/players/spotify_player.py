import yaml
import time as time
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .music_player import MusicPlayer
from buttons import RequestButtons

class SpotifyPlayer(MusicPlayer):
    def __init__(self, device_name='vintage-radio', report_interval=10, config_file='tracks.yml'):
        super().__init__()
        scope = "user-read-playback-state user-modify-playback-state"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        devices = self.sp.devices()
        for d in devices['devices']:
            print('device: ', d['name'], d['id'], end="\r\n")

        self.device_id = None
        for d in devices['devices']:
            if d['name'] == device_name:
                self.device_id = d['id']
                break

        self.last_asked = time.time()
        self.report_interval = report_interval
        self.next_report = time.time()
        self.sp.transfer_playback(self.device_id)
        self.info = None

        self.button_mapping = {
            RequestButtons.Button1: "https://open.spotify.com/album/6V9rvW05Um5bIHePPfeI8p", #Vows
            RequestButtons.Button2: "https://open.spotify.com/playlist/3yNdAPURGx5mBrs4t2vkRZ", #incredibox
            RequestButtons.Button3: "https://open.spotify.com/album/5VoeRuTrGhTbKelUfwymwu", #born to die
            RequestButtons.Button4: "https://open.spotify.com/album/2KSWrd22LGc0Hmqs2Z5i7z", # still live
            RequestButtons.Button5: "https://open.spotify.com/album/3qU4wXm0Qngbtnr5PiLbFX", # caravan
            RequestButtons.Button6: "https://open.spotify.com/playlist/02Jjjt6CHQW3lBq5Co5SCW", #Gotg Vol.1
            RequestButtons.Button7: "https://open.spotify.com/album/5XJ2NeBxZP3HFM8VoBQEUe", #bangarang
            RequestButtons.Button8: "https://open.spotify.com/album/2ANVost0y2y52ema1E9xAZ", #Thriller
            RequestButtons.Button9: "https://open.spotify.com/playlist/5b611EptDuCm5Pe8xCACTT", #Konoba
        }
        try:
            f = open(config_file)
            config = yaml.safe_load(f)
            for button in RequestButtons:
                if button.value in config:
                    self.button_mapping[button] = config[button.value]
        except Exception as e:
            print(e, end="\r\n")
            print('No config provided, using defaults', end="\r\n")
            pass

    def pause(self):
        self.sp.pause_playback(device_id=self.device_id)

    def play(self, link: str=None):
        self.sp.start_playback(device_id=self.device_id, context_uri=link)

    def next(self):
        self.sp.next_track(device_id=self.device_id)

    def previous(self):
        self.sp.previous_track(device_id=self.device_id)

    def switch(self, button: RequestButtons):
        self.play(link=self.button_mapping[button])

    def progress(self):
        now = time.time()
        if now > self.next_report or self.info is None:
            self.next_report = time.time() + self.report_interval
            self.info = self.sp.currently_playing()
            self.last_asked = time.time()
        total_time = self.info['item']['duration_ms'] / 1000.0

        since_last_report = now - self.last_asked
        cur_time = self.info['progress_ms'] / 1000.0 + since_last_report

        time_left = total_time - cur_time
        self.next_report = min(now + time_left, self.last_asked + self.report_interval)
        return cur_time / total_time

    def seek(self, time: float):
        info = self.sp.currently_playing()
        total_time = info['item']['duration_ms']
        self.sp.seek_track(int(total_time*time))
