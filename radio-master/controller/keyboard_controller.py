import tty
import termios

import sys
import select
from typing import Set
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

class KeyboardController(IOController):

    def __init__(self, device_name='vintage-radio', report_interval=10):
        super().__init__()
        self.save_mode()

    def set_raw_mode(self):
        tty.setcbreak(sys.stdin.fileno())

    def reset_mode(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.orig_settings)

    def save_mode(self):
        self.orig_settings = termios.tcgetattr(sys.stdin)

    def getRequests(self)->Set[RequestButtons]:
        active_requests = set()

        self.save_mode()
        self.set_raw_mode()
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0.0)
            if ready:
                char = sys.stdin.read(1)
                
                mapping = {str(i): getattr(RequestButtons, f"Button{i}") for i in range(1, 10)}
                
                if char in mapping:
                    active_requests.add(mapping[char])
        finally:
            self.reset_mode()

        return active_requests

    def getEffects(self)->Set[EffectButtons]:
        active_effects = set()
        return active_effects
