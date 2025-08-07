import time
import board
import busio
import displayio
import terminalio
import digitalio

from i2cdisplaybus import I2CDisplayBus
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_display_text import label

# — Power on peripherals (battery mode) —
vcc = digitalio.DigitalInOut(board.VCC_OFF)
vcc.direction = digitalio.Direction.OUTPUT
vcc.value = True
time.sleep(0.5)

# — Init display —
displayio.release_displays()
i2c = board.I2C()  # singleton bus
bus = I2CDisplayBus(i2c, device_address=0x3C, reset=None)
display = SSD1306(bus, width=128, height=64)

# — Build root group + black background —
root = displayio.Group()
display.root_group = root
bmp = displayio.Bitmap(128, 64, 1)
pal = displayio.Palette(1)
pal[0] = 0x000000
root.append(displayio.TileGrid(bmp, pixel_shader=pal, x=0, y=0))

# — Label for showing history (white, 2× scale) —
text_label = label.Label(terminalio.FONT, text="", scale=1)
text_label.x = 0
text_label.y = 0
root.append(text_label)

# — Button setup —
SW_PINS = [
    ("SW0", board.P1_04),
    ("SW1", board.P0_11),
    ("SW2", board.P1_00),
    ("SW3", board.P0_24),
    ("SW4", board.P1_06),
]
buttons = []
for name, pin in SW_PINS:
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    buttons.append((name, btn))

# — Press history list (max 4 lines) —
history = []

# — Main loop —
while True:
    for name, btn in buttons:
        if not btn.value:  # pressed (LOW)
            entry = f"{name} pressed"
            history.append(entry)
            # keep only last 4 entries
            history = history[-4:]
            # update display (newline-separated)
            text_label.text = "\n".join(history)
            print(entry)
            time.sleep(0.3)  # debounce
    time.sleep(0.01)
