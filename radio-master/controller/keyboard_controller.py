import tty
import termios

import sys
import select
from typing import Set, Tuple, Callable
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

class KeyboardController(IOController):

    def __init__(self, device_name='vintage-radio', report_interval=10):
        super().__init__()
        self.active_requests = set()
        self.active_effects = set()
        self.volume = 0.5

        self.volume_callback = None
        self.effect_callback = None
        self.request_callback = None

    def _set_raw_mode(self):
        self.orig_settings = termios.tcgetattr(sys.stdin)
        new = termios.tcgetattr(sys.stdin)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
        new[3] |= termios.ISIG 
        termios.tcsetattr(sys.stdin, termios.TCSANOW, new)
        # tty.setcbreak(sys.stdin.fileno())

    def _reset_mode(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.orig_settings)

    def setRequestCallback(self, callback: Callable[[RequestButtons], None]):
        self.request_callback = callback

    def setEffectCallback(self, callback: Callable[[EffectButtons, bool], None]):
        self.effect_callback = callback

    def setVolumeCallback(self, callback: Callable[[float, float], None]):
        self.volume_callback = callback

    def run_loop(self):
        self._set_raw_mode()
        try:
            while True:
                self.update()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self._reset_mode()

    def update(self):
        old_req = self.active_requests
        old_effects = self.active_effects
        old_volume = self.volume
        self.active_requests = set()
        self.active_effects = set()

        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        if ready:
            char = sys.stdin.read(1)
            if char == '\x1b':
                seq = sys.stdin.read(2)
                if seq == '[A':
                    self.volume += 0.1
                    self.volume = min(self.volume, 1)
                elif seq == '[B':
                    self.volume -= 0.1
                    self.volume = max(self.volume, 0)
            mapping = {str(i): getattr(RequestButtons, f"Button{i}") for i in range(1, 10)}
            
            if char in mapping:
                self.active_requests.add(mapping[char])

        if self.volume_callback and old_volume != self.volume:
            self.volume_callback(old_volume, self.volume)

        if self.request_callback and old_req != self.active_requests:
            new = self.active_requests - old_req
            for req in new:
                self.request_callback(req)

        if self.effect_callback and old_effects != self.effect_callback:
            added = self.active_effects - old_effects
            for n in added:
                self.effect_callback(n, True)

            deleted = old_effects - self.active_effects
            for d in deleted:
                self.effect_callback(d, False)
