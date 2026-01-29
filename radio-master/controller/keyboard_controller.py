import tty
import termios

import sys
import select
from typing import Set, Tuple, Callable
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

class KeyboardController(IOController):

    def __init__(self):
        super().__init__()
        self.active_requests = set()
        self.active_effects = set()
        self.volume = 0.5
        self.mod1 = 0.5
        self.mod2 = 0.5

        self.volume_callback = None
        self.effect_callback = None
        self.effect_value_callback = None
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

    def setOptionalValueCallback(self, callback: Callable[[float, float], None]):
        self.effect_value_callback = callback

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
        old_req = set(self.active_requests)
        old_effects = set(self.active_effects)
        old_volume = self.volume
        old_mods = (self.mod1, self.mod2)
        self.active_requests = set()

        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        if ready:
            char = sys.stdin.read(1)
            if char == '\x1b':
                seq = sys.stdin.read(2)
                if seq == '[A':
                    self.volume = min(self.volume + 0.1, 1)
                elif seq == '[B':
                    self.volume = max(self.volume - 0.1, 0)
                elif seq == '[D':
                    self.mod1 = max(self.mod1 - 0.1, 0)
                elif seq == '[C': # Right Arrow
                    self.mod1 = min(self.mod1 + 0.1, 1)

            req_mapping = {str(i): getattr(RequestButtons, f"Button{i}") for i in range(1, 10)}
            req_mapping[','] = RequestButtons.PauseButton
            req_mapping['.'] = RequestButtons.PlayButton
            req_mapping['n'] = RequestButtons.NextButton
            req_mapping['p'] = RequestButtons.PreviousButton
            
            if char in req_mapping:
                self.active_requests.add(req_mapping[char])

            effect_mapping = {
                'a': EffectButtons.Jazz,
                's': EffectButtons.Spatial3D,
                'v': EffectButtons.Voice,
                'b': EffectButtons.Bass,
                'o': EffectButtons.Orchestra,
            }
            if char in effect_mapping:
                effect = effect_mapping[char]
                if effect in self.active_effects:
                    self.active_effects.remove(effect)
                else:
                    self.active_effects.add(effect_mapping[char])

        if self.volume_callback and old_volume != self.volume:
            self.volume_callback(old_volume, self.volume)

        if self.request_callback and old_req != self.active_requests:
            new = self.active_requests - old_req
            for req in new:
                self.request_callback(req)

        if self.effect_callback and old_effects != self.active_effects:
            added = self.active_effects - old_effects
            for n in added:
                self.effect_callback(n, True)

            deleted = old_effects - self.active_effects
            for d in deleted:
                self.effect_callback(d, False)
        if self.effect_value_callback and old_mods != (self.mod1, self.mod2):
            self.effect_value_callback(self.mod1, self.mod2)
