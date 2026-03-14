import wiringpi
import time
from typing import Set, Tuple, Callable, Dict
from .controller import IOController
from buttons import RequestButtons
from buttons import EffectButtons

DEBOUNCE_MS = 40 
ANALOG_SMOOTH_ALPHA = 0.15
ANALOG_SMOOTH_ALPHA_VOLUME = 0.40
ANALOG_DEADZONE = 0.05

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
        self.old_volume = self.volume
        self.filt_volume = self.volume
        self.filt_mod1 = self.mod1
        self.filt_mod2 = self.mod2
        self.old_mods = (self.mod1, self.mod2)

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

        self.cache = {}
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
            
        self._led_cache = [[[-1, 0] for _ in range(3)] for _ in range(100)]
        self.LED_RETRANSMIT_INTERVAL = 0.5
        self.rotate_callback = None
        self.ENC_A = 52
        self.ENC_B = 53
        self.ENC_SW = 48

        for pin in [self.ENC_A, self.ENC_B, self.ENC_SW]:
            wiringpi.pinMode(pin, wiringpi.GPIO.INPUT)
            wiringpi.pullUpDnControl(pin, wiringpi.GPIO.PUD_UP)

        self.encoder_subticks = 0
        self.TICK_THRESHOLD = 3

        self.last_encoder_state = 0
        self.TRANSITIONS = [
            0, -1,  1,  0,  # 00 -> 00, 01, 10, 11 (11 is illegal)
            1,  0,  0, -1,  # 01 -> 00, 01, 10, 11 (10 is illegal)
           -1,  0,  0,  1,  # 10 -> 00, 01, 10, 11 (01 is illegal)
            0,  1, -1,  0   # 11 -> 00, 01, 10, 11 (00 is illegal)
        ]

    def setRequestCallback(self, callback: Callable[[RequestButtons], None]):
        self.request_callback = callback

    def setEffectCallback(self, callback: Callable[[EffectButtons, bool], None]):
        self.effect_callback = callback

    def setOptionalValueCallback(self, callback: Callable[[float, float], None]):
        self.effect_value_callback = callback

    def setVolumeCallback(self, callback: Callable[[float], None]):
        self.volume_callback = callback

    def _process_pin_event(self, pin: int) -> bool:
        current_state = wiringpi.digitalRead(pin)
        now = int(time.time() * 1000)
        is_click = False

        if current_state != self.last_state[pin]:
            self.last_change_time[pin] = now
            self.last_state[pin] = current_state

        if (now - self.last_change_time[pin]) > DEBOUNCE_MS:
            if self.stable_state[pin] != current_state:
                if self.stable_state[pin] == 1 and current_state == 0:
                    is_click = True
                self.stable_state[pin] = current_state
        
        return is_click

    def setEncoderRotateCallback(self, callback: Callable[[int], None]):
        self.rotate_callback = callback


    def _poll_encoder(self):
        a = wiringpi.digitalRead(self.ENC_A)
        b = wiringpi.digitalRead(self.ENC_B)
        
        current_state = (a << 1) | b
        
        if current_state != self.last_encoder_state:
            index = (self.last_encoder_state << 2) | current_state
            direction = self.TRANSITIONS[index]
            if direction != 0:
                self.encoder_subticks += direction
            
                if abs(self.encoder_subticks) >= self.TICK_THRESHOLD:
                    final_dir = -1 if self.encoder_subticks > 0 else 1
                    self.encoder_subticks = 0
                    
                    if self.rotate_callback:
                        self.rotate_callback(final_dir)
            
            self.last_encoder_state = current_state


    def _update_analogs(self):
        if self.i2c_fd < 0: return

        wiringpi.wiringPiI2CWrite(self.i2c_fd, 0)

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

        raw_mod1 = scale(raw[0], raw[1], *ranges['p5'])
        raw_volume = ( 1 - scale(raw[2], raw[3], *ranges['p4']))
        raw_mod2 = scale(raw[4], raw[5], *ranges['p3'])

        self.filt_mod1 = (ANALOG_SMOOTH_ALPHA * raw_mod1) + ((1 - ANALOG_SMOOTH_ALPHA) * self.filt_mod1)
        self.filt_volume = (ANALOG_SMOOTH_ALPHA_VOLUME * raw_volume) + ((1 - ANALOG_SMOOTH_ALPHA_VOLUME) * self.filt_volume)
        self.filt_mod2 = (ANALOG_SMOOTH_ALPHA * raw_mod2) + ((1 - ANALOG_SMOOTH_ALPHA) * self.filt_mod2)

        self.mod1 = self.filt_mod1
        self.volume = self.filt_volume
        self.mod2 = self.filt_mod2


    def update(self):
        old_effects = set(self.active_effects)

        self._update_analogs()
        self._poll_encoder()
        self._refresh_stale_leds()

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
        
        if self.volume_callback and abs(self.old_volume - self.volume) > 0.015:
            self.old_volume = self.volume
            self.volume_callback(self.volume)

        if self.effect_value_callback and (abs(self.old_mods[0] - self.mod1) > ANALOG_DEADZONE or abs(self.old_mods[1] - self.mod2) > ANALOG_DEADZONE):
            self.old_mods = (self.mod1, self.mod2)
            self.effect_value_callback(self.mod1, self.mod2)

        if self.effect_callback and old_effects != self.active_effects:
            added = self.active_effects - old_effects
            for e in added: self.effect_callback(e, True)
            deleted = old_effects - self.active_effects
            for e in deleted: self.effect_callback(e, False)

    def _send_led_packet(self, index: int, color_id: int, value: int, force=False):
        if self.i2c_fd < 0: return
        now = time.time()

        if not force:
            cached_val, last_sent = self._led_cache[index][color_id]
            if not force and cached_val == value and (now - last_sent) < self.LED_RETRANSMIT_INTERVAL:
                return

        if index < 100:
            self._led_cache[index][color_id] = [value, now]
        data = (value << 8) | (color_id & 0xFF)
        wiringpi.wiringPiI2CWriteReg16(self.i2c_fd, index, data)

    def _set_led_value(self, index: int, r: int, g: int, b: int, force=False):
        self._send_led_packet(index, 0, r, force=force)
        self._send_led_packet(index, 1, g, force=force)
        self._send_led_packet(index, 2, b, force=force)


    def _refresh_stale_leds(self, limit=2):
        count = 0
        now = time.time()
        
        for i in range(100):
            for channel in range(3):
                val, last_sent = self._led_cache[i][channel]
                if (now - last_sent) > self.LED_RETRANSMIT_INTERVAL:
                    self._send_led_packet(i, channel, val, force=True)
                    count += 1
                    if count >= limit: return

    def _update_strip_progress(self, start, end, pct, r, g, b, reverse=False):
        length = end - start + 1
        precise_num_on = pct * length

        for i in range(start, end + 1):
            distance = (end - i) if reverse else (i - start)

            if distance < int(precise_num_on):
                self._set_led_value(i, r, g, b)
            elif distance < precise_num_on:
                fraction = precise_num_on - int(precise_num_on)
                self._set_led_value(i, int(r * fraction), int(g * fraction), int(b * fraction))
            else:
                # Off
                self._set_led_value(i, 0, 0, 0)

    def _update_strip_selection(self, start, end, cur_idx, min_idx=0, max_idx=None, selection_idx=None, selection_color=(0, 255, 0), current_color=(255, 0, 0), delimiter_color=(255, 255, 255), reverse=False):
        if selection_idx is None:
            selection_idx = cur_idx
            
        strip_length = end - start + 1
        slots_per_page = strip_length // 2 
        
        current_page = selection_idx // slots_per_page
        local_selection_idx = selection_idx % slots_per_page
        
        playing_page = cur_idx // slots_per_page
        local_playing_idx = cur_idx % slots_per_page if playing_page == current_page else -1

        total_tracks = max_idx if max_idx is not None else 0
        tracks_on_this_page = total_tracks - (current_page * slots_per_page)

        for i in range(start, end + 1):
            distance = (end - i) if reverse else (i - start)
            slot_index = distance // 2

            if slot_index > tracks_on_this_page:
                self._set_led_value(i, 0, 0, 0)
                continue

            if distance % 2 == 0:
                self._set_led_value(i, *delimiter_color)
            else:
                slot_index = distance // 2
                
                if slot_index == local_selection_idx:
                    self._set_led_value(i, *selection_color)
                
                elif slot_index == local_playing_idx:
                    self._set_led_value(i, *current_color)
                
                else:
                    self._set_led_value(i, 0, 0, 0)

    def setStrip1Progress(self, pct: float, r: int, g: int, b: int):
        self._update_strip_progress(0, 46, pct, r, g, b, reverse=False)

    def setStrip2Progress(self, pct: float, r: int, g: int, b: int):
        self._update_strip_progress(47, 92, pct, r, g, b, reverse=True)

    def setStrip1Selection(self, idx: int, max_idx: int, selection_idx: int, **kwargs):
        self._update_strip_selection(0, 46, idx, max_idx=max_idx, selection_idx=selection_idx, reverse=False, **kwargs)

    def setStrip2Selection(self, idx: int, max_idx: int, selection_idx: int, **kwargs):
        self._update_strip_selection(47, 92, idx, max_idx=max_idx, selection_idx=selection_idx, reverse=True, **kwargs)
        
    def flushStrips(self):
        self._send_led_packet(255, 0, 0, force=True)

    def run_loop(self):
        print("Kontroler WiringController uruchomiony.")
        try:
            while True:
                self.update()
                wiringpi.delay(1) 
        except KeyboardInterrupt:
            print("\nZamykanie kontrolera...")
