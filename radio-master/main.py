from players.spotify_player import SpotifyPlayer
from controller.keyboard_controller import KeyboardController
from controller.wiring_controller import WiringController
from mixer.mixer import Mixer
from mixer.harmony import HarmonizerEffect
from mixer.flanger import FlangerEffect
from mixer.chorus import ChorusEffect
from mixer.reverb import ReverbEffect
from mixer.bass import BassBoostEffect
from buttons import EffectButtons
import time
import pulsectl
import wiringpi

device = "/dev/i2c-0"
i2caddr = 0x35
LED_MODE_VOLUME = 0
LED_MODE_EFFECT = 1
LED_MODE_SELECT = 2
rotation_window_ms = 2000 # Time window to detect the "double-turn" to enter Select Mode


volume_color = ( 252, 216, 35 )
progress_color = (242, 252, 194)

pending_index = 0
total_tracks = 1
last_rotate_time = 0
in_fast_select = False

effect_timeout_ms = 5000
select_timeout_ms = 7000
progress_time_ms = 150
album_progress = 0

led_mode = LED_MODE_VOLUME
last_effect_change = 0
last_select_change = 0
last_show_progress = time.time() * 1000

sp = SpotifyPlayer()

pulse = pulsectl.Pulse('volume-controller')
sink = pulse.sink_list()[0]

last_vol = 0
kc = WiringController()
fd = wiringpi.wiringPiI2CSetupInterface(device, i2caddr)

mx = Mixer()
mx.addEffect(HarmonizerEffect, effect_type=EffectButtons.Voice)
mx.addEffect(ReverbEffect, effect_type=EffectButtons.Jazz)
mx.addEffect(FlangerEffect, effect_type=EffectButtons.Spatial3D)
mx.addEffect(BassBoostEffect, effect_type=EffectButtons.Bass)
mx.addEffect(ChorusEffect, effect_type=EffectButtons.Orchestra)

def setEffect(e, active):
    print(f"Setting effect of {e} to {active}", end="\r\n")
    if active:
        mx.on(e)
    else:
        mx.off(e)
def setRequest(req):
    print(f"Request made: {req}", end="\r\n")
    sp.switch(req)

def setEffectValue(v1, v2):
    global led_mode, last_effect_change

    now = int(time.time() * 1000)

    led_mode = LED_MODE_EFFECT
    last_effect_change = now

    kc.setStrip1Progress(v2, 0, 255, 0)
    kc.setStrip2Progress(v1, 0, 0, 255)
    mx.setValue1(v1)
    mx.setValue2(v2)

def setVolume(vol):
    global led_mode, last_vol, last_effect_change, last_select_change
    pulse.volume_set_all_chans(sink, vol)
    last_effect_change -= effect_timeout_ms
    last_select_change -= effect_timeout_ms

    led_mode = LED_MODE_VOLUME
    last_vol = vol

def setRotate(rot):
    global led_mode, last_select_change, album_progress, pending_index, total_tracks, last_rotate_time, in_fast_select
    
    now = int(time.time() * 1000)
    direction = 1 if rot > 0 else -1
    
    current_idx, total_tracks = sp.get_queue_position()

    if (now - last_rotate_time) < rotation_window_ms:
        led_mode = LED_MODE_SELECT
        if not in_fast_select:
            print("--- ENTERING SELECT MODE ---")
            in_fast_select = True
            pending_index = current_idx
    
    last_rotate_time = now
    last_select_change = now 

    if in_fast_select:
        pending_index = (pending_index + direction) % total_tracks
        print(f"Selecting: {pending_index + 1}/{total_tracks}")
    else:
        if rot > 0:
            sp.next()
        else:
            sp.previous()
        album_progress = sp.get_queue_position()
    album_progress = sp.get_queue_position()

kc.setVolumeCallback(setVolume)
kc.setRequestCallback(setRequest)
kc.setEffectCallback(setEffect)
kc.setOptionalValueCallback(setEffectValue)
kc.setEncoderRotateCallback(setRotate)
try: 
    while True:
        kc.update()

        now = int(time.time() * 1000)

        if led_mode == LED_MODE_SELECT and (now - last_select_change) > select_timeout_ms:
            if in_fast_select:
                print(f"--- COMMITTING TO TRACK {pending_index + 1} ---")
                sp.jump_to_index(pending_index) 
                in_fast_select = False
            
            led_mode = LED_MODE_VOLUME
        if led_mode == LED_MODE_EFFECT and (now - last_effect_change) > effect_timeout_ms:
            led_mode = LED_MODE_VOLUME

        if (now - last_show_progress) > progress_time_ms:
            last_show_progress = now

            if led_mode == LED_MODE_VOLUME:

                kc.setStrip1Progress(last_vol, *volume_color)
                kc.setStrip2Progress(sp.progress(), *progress_color)

            elif led_mode == LED_MODE_SELECT:
                time_passed = now - last_select_change
                time_left = select_timeout_ms - time_passed
                
                if time_left > 6000:
                    blink_rate = select_timeout_ms
                elif time_left > 3500:
                    blink_rate = 500
                elif time_left > 1000:
                    blink_rate = 250
                is_on = ((now - last_select_change) // blink_rate) % 2 == 0
                
                s_color = (0, 255, 0) if is_on else (0, 0, 0)
                
                kc.setStrip1Selection(
                    album_progress[0], 
                    album_progress[1], 
                    selection_idx=pending_index, 
                    selection_color=s_color
                )
                
                kc.setStrip2Progress(sp.progress(), *progress_color)

        kc.flushStrips()
        wiringpi.delay(1)
except KeyboardInterrupt:
    print("\nClosing player...")
