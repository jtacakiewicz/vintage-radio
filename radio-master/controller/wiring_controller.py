import wiringpi
import time
from typing import Set, Tuple, Callable, Dict
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

DEBOUNCE_MS = 150

class WiringController(IOController):

    def __init__(self, effect_buttons: Dict[int, EffectButtons] = None, request_buttons: Dict[int, RequestButtons] = None):
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
        wiringpi.wiringPiSetupGpio()
        if effect_buttons == None:
            effect_buttons = {
                37: EffectButtons.Spatial3D,
                39: EffectButtons.Jazz,
                59: EffectButtons.Orchestra,
                63: EffectButtons.Bass,
                60: EffectButtons.Voice,
            }
        if request_buttons == None:
            request_buttons = {}
        self.effect_buttons = effect_buttons
        self.request_buttons = request_buttons

        self.last_state = {}
        self.stable_state = {}
        self.last_change_time = {}
        for pin in [*request_buttons.keys(), *effect_buttons.keys()]:
            wiringpi.pinMode(pin, wiringpi.GPIO.INPUT)
            wiringpi.pullUpDnControl(pin, wiringpi.GPIO.PUD_UP)
            self.last_state[pin] = wiringpi.digitalRead(pin)
            self.stable_state[pin] = self.last_state[pin]
            self.last_change_time[pin] = int(time.time() * 1000)


    def setRequestCallback(self, callback: Callable[[RequestButtons], None]):
        self.request_callback = callback

    def setEffectCallback(self, callback: Callable[[EffectButtons, bool], None]):
        self.effect_callback = callback

    def setOptionalValueCallback(self, callback: Callable[[float, float], None]):
        self.effect_value_callback = callback

    def setVolumeCallback(self, callback: Callable[[float, float], None]):
        self.volume_callback = callback

    def run_loop(self):
        try:
            while True:
                self.update()
                wiringpi.delay(1)
        except KeyboardInterrupt:
            print("Exiting controller", end="\r\n")

    def _process_pin(self, pin: int):
        current_state = wiringpi.digitalRead(pin)

        now = int(time.time() * 1000)
        if current_state != self.last_state[pin]:
            self.last_change_time[pin] = now
            self.last_state[pin] = current_state

        if self.stable_state[pin] != self.last_state[pin] and (now - self.last_change_time[pin]) > DEBOUNCE_MS:
            self.stable_state[pin] = self.last_state[pin]

    def update(self):
        old_req = set(self.active_requests)
        old_effects = set(self.active_effects)
        old_volume = self.volume
        old_mods = (self.mod1, self.mod2)
        self.active_requests = set()


        now = int(time.time() * 1000)
        for pin, effect in self.effect_buttons.items():
            self._process_pin(pin)
            if not self.stable_state[pin]:
                self.active_effects.add(effect)
            elif effect in self.active_effects:
                self.active_effects.remove(effect)

        # TODO

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
