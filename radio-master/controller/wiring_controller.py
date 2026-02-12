import wiringpi
import time
from typing import Set, Tuple, Callable, Dict
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

DEBOUNCE_MS = 40 

class WiringController(IOController):

    def __init__(self, effect_buttons: Dict[int, EffectButtons] = None, 
                 request_buttons: Dict[int, RequestButtons] = None, 
                 i2c_dev: str = "/dev/i2c-0", i2c_addr: int = 0x35):
        super().__init__()
        
        self.last_request = None
        self.active_effects = set()
        self.volume = 0.5
        self.mod1 = 0.5
        self.mod2 = 0.5

        self.volume_callback = None
        self.effect_callback = None
        self.effect_value_callback = None
        self.request_callback = None

        wiringpi.wiringPiSetupGpio()
        self.i2c_fd = wiringpi.wiringPiI2CSetupInterface(i2c_dev, i2c_addr)
        if self.i2c_fd < 0:
            print(f"BŁĄD: Nie można zainicjalizować I2C na {i2c_dev}")

        if effect_buttons is None:
            self.effect_buttons = {
                37: EffectButtons.Spatial3D,
                39: EffectButtons.Jazz,
                59: EffectButtons.Orchestra,
                63: EffectButtons.Bass,
                60: EffectButtons.Voice,
            }
        else:
            self.effect_buttons = effect_buttons

        if request_buttons is None:
            self.request_buttons = {
                50: RequestButtons.Button1,
                49: RequestButtons.Button2,
                56: RequestButtons.Button3,
                40: RequestButtons.Button4,
                46: RequestButtons.Button5,
                36: RequestButtons.Button6,
                61: RequestButtons.Button7,
                44: RequestButtons.Button8,
            }
        else:
            self.request_buttons = request_buttons

        self.last_state = {}
        self.stable_state = {}
        self.last_change_time = {}
        
        all_pins = list(self.request_buttons.keys()) + list(self.effect_buttons.keys())
        
        for pin in all_pins:
            wiringpi.pinMode(pin, wiringpi.GPIO.INPUT)
            wiringpi.pullUpDnControl(pin, wiringpi.GPIO.PUD_UP)
            initial_val = wiringpi.digitalRead(pin)
            self.last_state[pin] = initial_val
            self.stable_state[pin] = initial_val
            self.last_change_time[pin] = int(time.time() * 1000)

    def setRequestCallback(self, callback: Callable[[RequestButtons], None]):
        self.request_callback = callback

    def setEffectCallback(self, callback: Callable[[EffectButtons, bool], None]):
        self.effect_callback = callback

    def setOptionalValueCallback(self, callback: Callable[[float, float], None]):
        self.effect_value_callback = callback

    def setVolumeCallback(self, callback: Callable[[float], None]):
        self.volume_callback = callback

    def _process_pin_event(self, pin: int) -> bool:
        """
        Zwraca True tylko wtedy, gdy wykryto stabilne naciśnięcie (zbocze opadające).
        Używane dla Requestów, by nie ignorować kliknięć.
        """
        current_state = wiringpi.digitalRead(pin)
        now = int(time.time() * 1000)
        is_click = False

        if current_state != self.last_state[pin]:
            self.last_change_time[pin] = now
            self.last_state[pin] = current_state

        if (now - self.last_change_time[pin]) > DEBOUNCE_MS:
            if self.stable_state[pin] != current_state:
                # Jeśli zmiana ze stanu wysokiego (1) na niski (0) -> kliknięcie
                if self.stable_state[pin] == 1 and current_state == 0:
                    is_click = True
                self.stable_state[pin] = current_state
        
        return is_click

    def _update_analogs(self):
        """Odczyt i skalowanie potencjometrów przez I2C"""
        if self.i2c_fd < 0: return

        wiringpi.wiringPiI2CWrite(self.i2c_fd, 0)
        wiringpi.delay(1)

        raw = []
        for _ in range(6):
            raw.append(wiringpi.wiringPiI2CRead(self.i2c_fd))

        ranges = {
            'p5': (804, 1023),
            'p4': (0, 975),
            'p3': (605, 935)
        }

        def scale(msb, lsb, v_min, v_max):
            val = (msb << 8) | lsb
            res = (val - v_min) / (v_max - v_min)
            return min(max(res, 0.0), 1.0)

        self.mod1 = scale(raw[0], raw[1], *ranges['p5'])
        self.volume = scale(raw[2], raw[3], *ranges['p4'])
        self.mod2 = scale(raw[4], raw[5], *ranges['p3'])

    def update(self):
        old_effects = set(self.active_effects)
        old_volume = self.volume
        old_mods = (self.mod1, self.mod2)

        self._update_analogs()

        for pin, req in self.request_buttons.items():
            if self._process_pin_event(pin):
                if req == self.last_request:
                    continue
                self.last_request = req
                if self.request_callback:
                    self.request_callback(req)

        for pin, effect in self.effect_buttons.items():
            self._process_pin_event(pin) 
            if self.stable_state[pin] == 0:
                self.active_effects.add(effect)
            else:
                if effect in self.active_effects:
                    self.active_effects.remove(effect)
        
        if self.volume_callback and abs(old_volume - self.volume) > 0.01:
            self.volume_callback(self.volume)

        if self.effect_value_callback and (abs(old_mods[0] - self.mod1) > 0.01 or abs(old_mods[1] - self.mod2) > 0.01):
            self.effect_value_callback(self.mod1, self.mod2)

        if self.effect_callback and old_effects != self.active_effects:
            added = self.active_effects - old_effects
            for e in added: self.effect_callback(e, True)
            deleted = old_effects - self.active_effects
            for e in deleted: self.effect_callback(e, False)

    def _send_led_packet(self, index: int, color_id: int, value: int):
        if self.i2c_fd < 0: return
        data = (value << 8) | (color_id & 0xFF)
        wiringpi.wiringPiI2CWriteReg16(self.i2c_fd, index, data)

    def setStrip1(self, pct: float, r: int, g: int, b: int):
        start, end = 0, 46
        num_on = int(pct * (end - start + 1))
        
        for i in range(start, end + 1):
            if (i - start) < num_on:
                self._send_led_packet(i, 0, r) # Red
                self._send_led_packet(i, 1, g) # Green
                self._send_led_packet(i, 2, b) # Blue
            else:
                self._send_led_packet(i, 0, 0)
                self._send_led_packet(i, 1, 0)
                self._send_led_packet(i, 2, 0)

    def setStrip2(self, pct: float, r: int, g: int, b: int):
        start, end = 47, 92
        num_on = int(pct * (end - start + 1))
        
        for i in range(start, end + 1):
            if (i - start) < num_on:
                self._send_led_packet(i, 0, r)
                self._send_led_packet(i, 1, g)
                self._send_led_packet(i, 2, b)
            else:
                self._send_led_packet(i, 0, 0)
                self._send_led_packet(i, 1, 0)
                self._send_led_packet(i, 2, 0)
        
    def flushStrips(self):
        self._send_led_packet(255, 0, 0)

    def run_loop(self):
        print("Kontroler WiringController uruchomiony.")
        try:
            while True:
                self.update()
                wiringpi.delay(1) 
        except KeyboardInterrupt:
            print("\nZamykanie kontrolera...")
