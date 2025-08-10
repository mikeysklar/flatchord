import time
import digitalio
import board
import displayio
from i2cdisplaybus import I2CDisplayBus
from adafruit_displayio_ssd1306 import SSD1306
import terminalio
from adafruit_display_text import label
import chords_config

# Power on peripherals if needed
vcc = digitalio.DigitalInOut(board.VCC_OFF)
vcc.direction = digitalio.Direction.OUTPUT
vcc.value = True
time.sleep(0.5)

displayio.release_displays()

i2c = board.I2C()
bus = I2CDisplayBus(i2c, device_address=0x3C, reset=None)
display = SSD1306(bus, width=128, height=64)

display_group = displayio.Group(scale=1, x=0, y=10)
display.root_group = display_group

text_buffer = ""
text_label = label.Label(terminalio.FONT, text=text_buffer, color=0xFFFFFF)
display_group.append(text_label)

SW_PINS = (
    board.P1_04,  # SW0
    board.P0_11,  # SW1
    board.P1_00,  # SW2
    board.P0_24,  # SW3
    board.P1_06,  # SW4
)

pins = []
for gp in SW_PINS:
    p = digitalio.DigitalInOut(gp)
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.UP
    pins.append(p)

# ─── USB HID setup (start OFF) ─────────────────────────────────────────
usbmode = False
keyboard = mouse = cc = None

def enable_hid():
    global usbmode, keyboard, mouse, cc, Keycode, ConsumerControlCode
    import usb_hid
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.mouse import Mouse
    from adafruit_hid.consumer_control import ConsumerControl
    from adafruit_hid.consumer_control_code import ConsumerControlCode
    from adafruit_hid.keycode import Keycode
    keyboard = Keyboard(usb_hid.devices)
    mouse = Mouse(usb_hid.devices)
    cc = ConsumerControl(usb_hid.devices)
    usbmode = True
    print("USB HID enabled")

def disable_hid():
    global usbmode, keyboard, mouse, cc
    keyboard = mouse = cc = None
    usbmode = False
    print("USB HID disabled")

# ─── Timing constants ────────────────────────────────────────────────
STABLE_MS_ALPHA = 0.03
STABLE_MS_OTHER = 0.02
DEBOUNCE_UP      = 0.05
TAP_WINDOW       = 0.5
MIN_TAP_INT      = 0.1
L5_REPEAT_MS     = 0.1
NAV_REPEAT_MS    = 0.2
LAYER_LOCK_COOLDOWN = 0.1
SCROLL_REPEAT_MS  = 0.15
THUMB_HOLD_TO_LOCK = 0.12

# ─── State variables ────────────────────────────────────────────────
layer            = 1
thumb_taps       = 0
tap_in_prog      = False
last_tap_time    = 0.0
last_combo       = ()
pending_combo    = None
sent_release     = False
skip_scag        = False
scag_skip_combo  = None
modifier_armed   = False
held_modifier    = None
last_time        = time.monotonic()
held_combo       = ()
last_repeat      = 0.0
accel_active     = False
held_nav_combo   = ()
last_nav         = 0.0
last_pending_combo = None
last_layer_change = 0.0
held_scroll_combo = ()
last_scroll       = 0.0
last_thumb_rise    = 0.0
thumb_locked       = False

# ─── Mouse chords for layer-7 ────────────────────────────────────────
MOVE_DELTA = 5
ACCEL_MULTIPLIER = 2
ACCEL_CHORD = (1, 2, 3)

# ─── Core chord logic ────────────────────────────────────────────────
def check_chords():
    global layer, thumb_taps, last_tap_time
    global last_combo, pending_combo, sent_release, skip_scag, scag_skip_combo
    global modifier_armed, held_modifier, last_time, last_repeat, accel_active
    global held_nav_combo, last_nav, held_combo, last_pending_combo
    global held_scroll_combo, last_scroll, text_buffer, text_label
    global usbmode

    now     = time.monotonic()
    pressed = tuple(not p.value for p in pins)
    combo   = tuple(i for i, down in enumerate(pressed) if down)

    # ─── A) Pure-thumb release ⇒ layer-lock ───────────────────────────
    if last_combo == (4,) and combo == ():
        if now - last_tap_time < TAP_WINDOW:
            thumb_taps += 1
        else:
            thumb_taps = 1
        last_tap_time = now
        layer = min(thumb_taps, 7)
        print(f"→ locked to layer-{layer}")
        pending_combo = None
        sent_release  = False
        skip_scag     = False
        modifier_armed = False
        held_modifier = None
        scag_skip_combo = None
        held_scroll_combo = ()
        last_combo = combo
        return

    # ─── B) Stabilize into pending_combo ──────────────────────────────
    if combo != last_combo:
        last_time = now
        if last_combo == () and combo != ():
            pending_combo = None
            sent_release  = False

    ms = STABLE_MS_ALPHA if layer == 1 else STABLE_MS_OTHER
    if combo and (now - last_time) >= ms and combo != pending_combo:
        pending_combo = combo

    pending_changed    = (pending_combo != last_pending_combo)
    last_pending_combo = pending_combo

    lm = chords_config.layer_maps[layer]

    # ─── Special: Layer‑3 chord (0,1,2,3,4) → toggle HID ──────────────
    if layer == 3 and combo == (0,1,2,3,4) and combo != last_combo:
        if not usbmode:
            enable_hid()
        else:
            disable_hid()
        text_label.text = "HID: ON" if usbmode else "HID: OFF"
        last_combo = combo
        sent_release = True
        time.sleep(0.3)  # debounce
        return

    # ─── macOS media keys ─────────────────────────────────────────────
    if usbmode and layer == 6:
        if combo and combo != last_combo and combo in lm:
            code = lm[combo]
            cc.send(code)
            sent_release = True
            time.sleep(DEBOUNCE_UP)

    # ─── Layer-4 SCAG “arm” ───────────────────────────────────────────
    if layer == 4 and not modifier_armed and pending_combo in chords_config.scag:
        held_modifier   = chords_config.scag[pending_combo]
        modifier_armed  = True
        scag_skip_combo = pending_combo
        skip_scag       = True
        pending_combo   = None
        last_combo      = ()
        return

    # ─── Layer-5: Mouse ───────────────────────────────────────────────
    if usbmode and layer == 5:
        accel_active = (pending_combo == chords_config.ACCEL_CHORD)

        if pending_combo in chords_config.mouse_button_chords and pending_changed:
            mouse.click(chords_config.mouse_button_chords[pending_combo])
            held_combo   = ()
            sent_release = True
            time.sleep(DEBOUNCE_UP)
            return

        if pending_combo in chords_config.mouse_scroll_chords and pending_changed:
            amt = chords_config.mouse_scroll_chords[pending_combo]
            if accel_active: amt *= ACCEL_MULTIPLIER
            mouse.move(wheel=amt)
            held_scroll_combo = pending_combo
            last_scroll       = now
            sent_release      = True
            return

        if (
            pending_combo == held_scroll_combo
            and pending_combo in chords_config.mouse_scroll_chords
            and (now - last_scroll) >= SCROLL_REPEAT_MS
        ):
            amt = chords_config.mouse_scroll_chords[pending_combo]
            if accel_active: amt *= ACCEL_MULTIPLIER
            mouse.move(wheel=amt)
            last_scroll = now
            return

        if pending_combo in chords_config.mouse_move_chords and pending_changed:
            dx, dy = chords_config.mouse_move_chords[pending_combo]
            if accel_active: dx *= ACCEL_MULTIPLIER; dy *= ACCEL_MULTIPLIER
            mouse.move(dx, dy)
            held_combo   = pending_combo
            last_repeat  = now
            sent_release = True
            return

        if pending_combo == held_combo \
           and pending_combo in chords_config.mouse_move_chords \
           and (now - last_repeat) >= L5_REPEAT_MS:
            dx, dy = chords_config.mouse_move_chords[held_combo]
            if accel_active: dx *= ACCEL_MULTIPLIER; dy *= ACCEL_MULTIPLIER
            mouse.move(dx, dy)
            last_repeat = now
            return

        if pending_combo in chords_config.mouse_hold_chords and pending_changed:
            mouse.press(chords_config.mouse_hold_chords[pending_combo])
            held_combo   = ()
            sent_release = True
            return

        if pending_combo in chords_config.mouse_release_chords and pending_changed:
            mouse.release(chords_config.mouse_release_chords[pending_combo])
            held_combo   = ()
            sent_release = True
            return

    # ─── First-release send for layers 1–3,6-7 ───────────────────────
    if len(combo) < len(last_combo) and last_combo and not sent_release:
        if skip_scag and last_combo == scag_skip_combo:
            skip_scag = False
        else:
            use = pending_combo or last_combo
            if layer == 4 and modifier_armed and last_combo in chords_config.alpha and usbmode:
                key = chords_config.alpha[last_combo]
                keyboard.press(held_modifier, key)
                keyboard.release_all()
                layer           = 1
                thumb_taps      = 1
                modifier_armed  = False
                skip_scag       = False

            elif layer in (1, 2, 3, 6, 7):
                # Skip HID toggle chord (layer‑3, (0,1,2,3,4))
                if use != (4,) and not (layer == 3 and use == (0,1,2,3,4)):
                    kc = lm.get(use)
                    if kc:
                        if usbmode:
                            keyboard.press(kc)
                            keyboard.release_all()

                        if kc == 61:  # handled above
                            pass
                        elif kc == 42:  # Backspace
                            text_buffer = text_buffer[:-1]
                            text_label.text = text_buffer
                        else:
                            if 4 <= kc <= 29:  # A-Z
                                char = chr(kc - 4 + ord('a'))
                            elif 30 <= kc <= 38:  # 1-9
                                char = chr(kc - 30 + ord('1'))
                            elif kc == 39:
                                char = "0"
                            elif kc == 44:
                                char = " "
                            else:
                                char = "?"
                            MAX_CHARS = display.width // (6 * display_group.scale)
                            lines = text_buffer.split("\n")
                            if len(lines[-1]) >= MAX_CHARS:
                                text_buffer += "\n" + char
                            else:
                                text_buffer += char
                            text_label.text = text_buffer

        sent_release = True
        time.sleep(DEBOUNCE_UP)

    if not combo and last_combo:
        pending_combo  = None
        sent_release   = False
        held_nav_combo = ()
        skip_layer_lock = False

    last_combo = combo

# ─── Main loop ───────────────────────────────────────────────────────
while True:
    check_chords()
    time.sleep(0.01)
