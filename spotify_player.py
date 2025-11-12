from music_player import MusicPlayer
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time as time

class SpotifyPlayer(MusicPlayer):
    def __init__(self, device_name='vintage-radio', report_interval=10):
        super().__init__()
        scope = "user-read-playback-state user-modify-playback-state"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        devices = self.sp.devices()
        for d in devices['devices']:
            print('device: ', d['name'], d['id'])

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


