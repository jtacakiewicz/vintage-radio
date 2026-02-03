import wiringpi
import time
from typing import Set, Tuple, Callable, Dict
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

# Zmniejszony debounce, aby nie ignorować szybkich kliknięć
DEBOUNCE_MS = 40 

class WiringController(IOController):

    def __init__(self, effect_buttons: Dict[int, EffectButtons] = None, 
                 request_buttons: Dict[int, RequestButtons] = None, 
                 i2c_dev: str = "/dev/i2c-0", i2c_addr: int = 0x35):
        super().__init__()
        
        # Stan wewnętrzny
        self.active_requests = set()
        self.active_effects = set()
        self.volume = 0.5
        self.mod1 = 0.5
        self.mod2 = 0.5

        # Callbacks
        self.volume_callback = None
        self.effect_callback = None
        self.effect_value_callback = None
        self.request_callback = None

        # Inicjalizacja sprzętu
        wiringpi.wiringPiSetupGpio()
        self.i2c_fd = wiringpi.wiringPiI2CSetupInterface(i2c_dev, i2c_addr)
        if self.i2c_fd < 0:
            print(f"BŁĄD: Nie można zainicjalizować I2C na {i2c_dev}")

        # Mapowanie przycisków efektów
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

        # Mapowanie przycisków żądań (Request)
        if request_buttons is None:
            self.request_buttons = {
                50: RequestButtons.Button1, # Dopasuj nazwy do swojego Enuma
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

        # Struktury do debouncingu i wykrywania zboczy
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

        # Dummy write, by zresetować wskaźnik w ATtiny
        wiringpi.wiringPiI2CWrite(self.i2c_fd, 0)
        wiringpi.delay(1)

        raw = []
        for _ in range(6):
            raw.append(wiringpi.wiringPiI2CRead(self.i2c_fd))

        # Zakresy kalibracji podane przez Ciebie
        ranges = {
            'p5': (804, 1023), # Mod 1
            'p4': (0, 975),   # Volume
            'p3': (605, 935)   # Mod 2
        }

        def scale(msb, lsb, v_min, v_max):
            val = (msb << 8) | lsb
            res = (val - v_min) / (v_max - v_min)
            return min(max(res, 0.0), 1.0)

        self.mod1 = scale(raw[0], raw[1], *ranges['p5'])
        self.volume = scale(raw[2], raw[3], *ranges['p4'])
        self.mod2 = scale(raw[4], raw[5], *ranges['p3'])

    def update(self):
        # Zapamiętanie starych stanów do porównania (histereza)
        old_effects = set(self.active_effects)
        old_volume = self.volume
        old_mods = (self.mod1, self.mod2)

        # 1. Aktualizacja potencjometrów
        self._update_analogs()

        # 2. Przetwarzanie Requestów (Zasada zdarzeniowa / Edge Detection)
        for pin, req in self.request_buttons.items():
            if self._process_pin_event(pin):
                if self.request_callback:
                    self.request_callback(req)

        # 3. Przetwarzanie Efektów (Zasada ciągła / Hold)
        for pin, effect in self.effect_buttons.items():
            # Aktualizujemy stable_state dla pinów efektów (bez zwracania zdarzenia)
            self._process_pin_event(pin) 
            if self.stable_state[pin] == 0: # Wciśnięty
                self.active_effects.add(effect)
            else: # Puszczony
                if effect in self.active_effects:
                    self.active_effects.remove(effect)

        # 4. Wywołanie pozostałych callbacków przy zmianie
        
        # Głośność (próg zmiany 1%)
        if self.volume_callback and abs(old_volume - self.volume) > 0.01:
            self.volume_callback(self.volume)

        # Modulatory (P5 i P3)
        if self.effect_value_callback and (abs(old_mods[0] - self.mod1) > 0.01 or abs(old_mods[1] - self.mod2) > 0.01):
            self.effect_value_callback(self.mod1, self.mod2)

        # Przełączniki efektów (On/Off)
        if self.effect_callback and old_effects != self.active_effects:
            added = self.active_effects - old_effects
            for e in added: self.effect_callback(e, True)
            deleted = old_effects - self.active_effects
            for e in deleted: self.effect_callback(e, False)

    def run_loop(self):
        print("Kontroler WiringController uruchomiony.")
        try:
            while True:
                self.update()
                # Mały delay, by nie zająć 100% CPU i dać czas I2C
                wiringpi.delay(1) 
        except KeyboardInterrupt:
            print("\nZamykanie kontrolera...")
