import yaml
import time as time
import socket
import threading
import os
import json
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
        self.sp.volume(volume_percent=100, device_id=self.device_id)
        self.info = {}
        self.last_updated_at = time.time()

        self.socket_path = "/tmp/librespot_event.sock"
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.server_socket.bind(self.socket_path)
        os.chmod(self.socket_path, 0o666)
        
        # Start a background thread to listen for Librespot events
        self.listener_thread = threading.Thread(target=self._listen_for_events, daemon=True)
        self.listener_thread.start()

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
        return self.sp.next_track(device_id=self.device_id)

    def previous(self):
        return self.sp.previous_track(device_id=self.device_id)

    def switch(self, button: RequestButtons):
        if button == RequestButtons.PlayButton:
            self.play()
        elif button == RequestButtons.PauseButton:
            self.pause()
        elif button == RequestButtons.NextButton:
            self.next()
        elif button == RequestButtons.PreviousButton:
            self.previous()
        elif button in self.button_mapping:
            self.play(link=self.button_mapping[button])
        else:
            print(f'ERROR: no mapping to {button} for spotify player', end='\r\n')

    def _listen_for_events(self):
        print("Listening worker");
        while True:
            raw_data, _ = self.server_socket.recvfrom(4096)
            try:
                event_data = json.loads(raw_data.decode('utf-8'))
                self._update_internal_state(event_data)
            except Exception as e:
                print(f"Error parsing event: {e}")

    def _update_internal_state(self, data):
        event = data.get('PLAYER_EVENT')
        if 'POSITION_MS' in data:
            self.last_updated_at = time.time()
            self.info['progress_ms'] = int(data.get('POSITION_MS', 0))

        if "TRACK_ID" in data and event == 'track_changed':
            self.info = {
                'is_playing': data.get('PLAYER_EVENT') == 'playing',
                'progress_ms': int(data.get('POSITION_MS', 0)),
                'item': {
                    'name': data.get('NAME'),
                    'artists': [{'name': data.get('ARTISTS')}],
                    'album': {
                        'name': data.get('ALBUM'),
                        'total_tracks': int(data.get('ALBUM_TRACKS', 1)) 
                    },
                    'duration_ms': int(data.get('DURATION_MS', 0)),
                    'uri': data.get('URI'),
                    'track_number': int(data.get('NUMBER', 1))
                }
            }
            print(f"Sync: {self.info['item']['artists'][0]['name']} - {self.info['item']['name']}")
            self._current_collection_total = None

        if event == 'playing':
            if self.info:
                self.info['is_playing'] = True
                if 'POSITION_MS' in data:
                    self.info['progress_ms'] = int(data.get('POSITION_MS'))
                self.last_updated_at = time.time()

        elif event in ['paused', 'stopped']:
            if self.info:
                if self.info['is_playing']:
                    elapsed = (time.time() - self.last_updated_at) * 1000
                    self.info['progress_ms'] += elapsed

                self.info['is_playing'] = False
                self.last_updated_at = time.time()
        if data.get('PLAYER_EVENT') in ['paused', 'stopped']:
            if self.info: self.info['is_playing'] = False

    def progress(self):
        if not self.info or not self.info.get('item'):
            return 0.0

        total_ms = self.info['item']['duration_ms']
        if total_ms == 0: return 0.0

        elapsed_ms = 0
        if self.info.get('is_playing'):
            elapsed_ms = (time.time() - self.last_updated_at) * 1000

        current_progress_ms = self.info['progress_ms'] + elapsed_ms
        return min(current_progress_ms / total_ms, 1.0)

    def get_queue_position(self):
        librespot_idx = 0
        if self.info and self.info.get('item'):
            librespot_idx = self.info['item'].get('track_number', 1) - 1

        current_uri = self.info['item'].get('uri') if self.info and self.info.get('item') else None

        if hasattr(self, '_cached_total') and getattr(self, '_last_uri', None) == current_uri:
            return (self._cached_index, self._cached_total)

        try:
            playback = self.sp.current_playback()

            if not playback or not playback.get('item'):
                return (librespot_idx, 1)

            if not playback.get('context'):
                total = playback['item']['album']['total_tracks']
                self._update_cache(librespot_idx, total, current_uri)
                return (librespot_idx, total)

            context = playback['context']
            print(context)
            ctype = context.get('type')
            curi = context.get('uri')

            if ctype == 'album':
                total = playback['item']['album']['total_tracks']
                self._update_cache(librespot_idx, total, current_uri)
                return (librespot_idx, total)

            if ctype == "collection":
                found_idx = -1
                offset = 0
                total = 0

                while True:
                    res = self.sp.current_user_saved_tracks(
                        offset=offset,
                        limit=50
                    )

                    items = res.get("items", [])
                    total = res.get("total", 0)

                    if not items:
                        break

                    for i, item in enumerate(items):
                        track = item.get("track")
                        if track and track.get("uri") == current_uri:
                            found_idx = offset + i
                            break

                    if found_idx != -1 or len(items) < 50:
                        break

                    offset += 50

                final_idx = found_idx if found_idx != -1 else librespot_idx
                self._update_cache(final_idx, total, current_uri)
                return (final_idx, total)
        except Exception:
            pass

        return (librespot_idx, 1)


    def _update_cache(self, idx, total, uri):
        self._cached_index = idx
        self._cached_total = total
        self._last_uri = uri


    def seek(self, time: float):
        info = self.sp.currently_playing()
        total_time = info['item']['duration_ms']
        self.sp.seek_track(int(total_time*time))
