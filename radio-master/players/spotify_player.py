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
            print("Got data");
            try:
                event_data = json.loads(raw_data.decode('utf-8'))
                self._update_internal_state(event_data)
                print(f"Parsing: {event_data}")
            except Exception as e:
                print(f"Error parsing event: {e}")

    def _update_internal_state(self, data):
        event = data.get('PLAYER_EVENT')
        if 'POSITION_MS' in data:
            self.last_updated_at = time.time()
            self.info['progress_ms'] = int(data.get('POSITION_MS', 0))

        # Check if we have enough data to build a mini 'info' object
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
                # If librespot sends a position with the play event, use it
                if 'POSITION_MS' in data:
                    self.info['progress_ms'] = int(data.get('POSITION_MS'))
                self.last_updated_at = time.time()

            # 3. Handle Pause/Stop
        elif event in ['paused', 'stopped']:
            if self.info:
                # Capture the exact progress at the moment of pausing
                if self.info['is_playing']:
                    elapsed = (time.time() - self.last_updated_at) * 1000
                    self.info['progress_ms'] += elapsed

                self.info['is_playing'] = False
                self.last_updated_at = time.time()
        # If the event is 'stop' or 'pause', update playing status
        if data.get('PLAYER_EVENT') in ['paused', 'stopped']:
            if self.info: self.info['is_playing'] = False

    def progress(self):
        if not self.info or not self.info.get('item'):
            return 0.0

        total_ms = self.info['item']['duration_ms']
        if total_ms == 0: return 0.0

        # Calculate live progress
        elapsed_ms = 0
        if self.info.get('is_playing'):
            elapsed_ms = (time.time() - self.last_updated_at) * 1000

        current_progress_ms = self.info['progress_ms'] + elapsed_ms
        return min(current_progress_ms / total_ms, 1.0)

    def get_queue_position(self):
        """
        Returns (current_index, total_tracks). 
        Correctly distinguishes between Album index and Playlist index.
        """
        # 1. Fallback to Librespot's Metadata (Correct for Albums)
        librespot_idx = 0
        if self.info and self.info.get('item'):
            librespot_idx = self.info['item'].get('track_number', 1) - 1

        # 2. Check Cache to save API calls
        current_uri = self.info['item'].get('uri') if self.info else None
        if hasattr(self, '_cached_total') and self._last_uri == current_uri:
            return (self._cached_index, self._cached_total)

        try:
            playback = self.sp.current_playback()
            
            # --- Case A: No active API context (Liked Songs / Single Track) ---
            if not playback or not playback.get('context'):
                total = playback['item']['album']['total_tracks'] if playback else 1
                self._update_cache(librespot_idx, total, current_uri)
                return (librespot_idx, total)

            context = playback['context']
            ctype = context['type'] # 'album', 'playlist', 'artist'
            curi = context['uri']

            # --- Case B: Album ---
            if ctype == 'album':
                # Librespot's index is perfect for albums. Just get the total.
                total = playback['item']['album']['total_tracks']
                self._update_cache(librespot_idx, total, current_uri)
                return (librespot_idx, total)

            # --- Case C: Playlist (The Search Logic) ---
            if ctype == 'playlist':
                found_idx = -1
                # Search the playlist to find which index our current URI is at
                # We paginate (100 at a time) to handle long playlists
                offset = 0
                total = 0
                while offset < 1000: # Search limit for performance
                    res = self.sp.playlist_items(curi, offset=offset, limit=100, 
                                                 fields='items(track(uri,id)),total')
                    total = res['total']
                    if not res['items']: break
                    
                    for i, item in enumerate(res['items']):
                        track = item.get('track')
                        if track and (track['uri'] == current_uri or track['id'] in current_uri):
                            found_idx = offset + i
                            break
                    
                    if found_idx != -1 or len(res['items']) < 100:
                        break
                    offset += 100
                
                # If we found it in the playlist, use that index. 
                # Otherwise, fallback to the album index to avoid showing 0.
                final_idx = found_idx if found_idx != -1 else librespot_idx
                self._update_cache(final_idx, total, current_uri)
                return (final_idx, total)

        except Exception as e:
            # Silence API errors and return Librespot fallback
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
