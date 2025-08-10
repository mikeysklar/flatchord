import time
import board
import busio
import displayio
from adafruit_displayio_ssd1306 import SSD1306
import digitalio
from adafruit_display_text import label
import terminalio

# — Power on peripherals (battery mode) —
vcc = digitalio.DigitalInOut(board.VCC_OFF)
vcc.direction = digitalio.Direction.OUTPUT
vcc.value = True
time.sleep(0.5)

displayio.release_displays()

i2c = busio.I2C(board.SCL, board.SDA)

display = SSD1306(i2c, width=128, height=64)

group = displayio.Group()
display.root_group = group

text_label = label.Label(terminalio.FONT, text="Hello!", color=0xFFFFFF, x=0, y=10)
group.append(text_label)

# Setup buttons
SW_PINS = (
    board.P1_04,  # SW0
    board.P0_11,  # SW1
    board.P1_00,  # SW2
    board.P0_24,  # SW3
    board.P1_06,  # SW4
)
pins = []
for pin in SW_PINS:
    p = digitalio.DigitalInOut(pin)
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.UP
    pins.append(p)

while True:
    pressed = [not p.value for p in pins]
    text_label.text = "Buttons: " + "".join(["1" if x else "0" for x in pressed])
    time.sleep(0.1)
