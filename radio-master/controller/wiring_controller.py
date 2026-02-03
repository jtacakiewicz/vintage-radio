import wiringpi
import time
from typing import Set, Tuple, Callable, Dict
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

DEBOUNCE_MS = 150

class WiringController(IOController):

    def __init__(self, effect_buttons: Dict[int, EffectButtons] = None, request_buttons: Dict[int, RequestButtons] = None, i2c_dev: str = "/dev/i2c-0", i2c_addr: int = 0x35):
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

        # Setup GPIO
        wiringpi.wiringPiSetupGpio()
        
        # Setup I2C
        self.i2c_fd = wiringpi.wiringPiI2CSetupInterface(i2c_dev, i2c_addr)
        if self.i2c_fd < 0:
            print(f"Warning: Could not initialize I2C on {i2c_dev}")

        if effect_buttons is None:
            effect_buttons = {
                37: EffectButtons.Spatial3D,
                39: EffectButtons.Jazz,
                59: EffectButtons.Orchestra,
                63: EffectButtons.Bass,
                60: EffectButtons.Voice,
            }
        
        self.effect_buttons = effect_buttons
        if request_buttons is None:
            request_buttons = {
                50: RequestButtons.Button1,
                49: RequestButtons.Button2,
                56: RequestButtons.Button3,
                40: RequestButtons.Button4,
                46: RequestButtons.Button5,
                36: RequestButtons.Button6,
                61: RequestButtons.Button7,
                44: RequestButtons.Button8,
            }
        self.request_buttons = request_buttons

        # Inicjalizacja stanów pinów
        self.last_state = {}
        self.stable_state = {}
        self.last_change_time = {}
        
        for pin in [*self.request_buttons.keys(), *self.effect_buttons.keys()]:
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

    def setVolumeCallback(self, callback: Callable[[float], None]):
        self.volume_callback = callback

    def _process_pin(self, pin: int):
        current_state = wiringpi.digitalRead(pin)
        now = int(time.time() * 1000)

        if current_state != self.last_state[pin]:
            self.last_change_time[pin] = now
            self.last_state[pin] = current_state

        if self.stable_state[pin] != self.last_state[pin] and (now - self.last_change_time[pin]) > DEBOUNCE_MS:
            self.stable_state[pin] = self.last_state[pin]

    def _update_analogs(self):
        if self.i2c_fd < 0: return

        # Trigger odczytu na ATtiny i reset pointera
        wiringpi.wiringPiI2CWrite(self.i2c_fd, 0)
        wiringpi.delay(1)

        raw_data = []
        for _ in range(6):
            raw_data.append(wiringpi.wiringPiI2CRead(self.i2c_fd))

        # Kalibracja zgodnie z Twoimi pomiarami
        p5_min, p5_max = 804, 1023
        p4_min, p4_max = 0, 975
        p3_min, p3_max = 605, 935

        # Obliczanie wartości 0.0 - 1.0
        def scale(raw, v_min, v_max):
            val = ((raw[0] << 8) | raw[1])
            res = (val - v_min) / (v_max - v_min)
            return min(max(res, 0.0), 1.0)

        self.mod1 = scale(raw_data[0:2], p5_min, p5_max)  # P5
        self.volume = scale(raw_data[2:4], p4_min, p4_max) # P4
        self.mod2 = scale(raw_data[4:6], p3_min, p3_max)  # P3

    def update(self):
        old_req = set(self.active_requests)
        old_effects = set(self.active_effects)
        old_volume = self.volume
        old_mods = (self.mod1, self.mod2)

        # 1. Odczyt analogów przez I2C
        self._update_analogs()

        # 2. Odczyt przycisków
        for pin, effect in self.effect_buttons.items():
            self._process_pin(pin)
            if not self.stable_state[pin]: # 0 = Pressed
                self.active_effects.add(effect)
            elif effect in self.active_effects:
                self.active_effects.remove(effect)

        for pin, req in self.request_buttons.items():
            self._process_pin(pin)
            if not self.stable_state[pin]:
                self.active_requests.add(req)

        # 3. Wywołanie callbacków (tylko jeśli nastąpiła zmiana)
        if self.volume_callback and abs(old_volume - self.volume) > 0.01:
            self.volume_callback(self.volume)

        if self.effect_value_callback and (abs(old_mods[0] - self.mod1) > 0.01 or abs(old_mods[1] - self.mod2) > 0.01):
            self.effect_value_callback(self.mod1, self.mod2)

        if self.request_callback and old_req != self.active_requests:
            new_reqs = self.active_requests - old_req
            for r in new_reqs:
                self.request_callback(r)

        if self.effect_callback and old_effects != self.active_effects:
            added = self.active_effects - old_effects
            for e in added: self.effect_callback(e, True)
            
            deleted = old_effects - self.active_effects
            for e in deleted: self.effect_callback(e, False)

    def run_loop(self):
        try:
            while True:
                self.update()
                wiringpi.delay(5) # Zwiększyłem odrobinę, by nie obciążać CPU i I2C
        except KeyboardInterrupt:
            print("\nExiting controller")
