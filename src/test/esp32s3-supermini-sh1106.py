import board, busio, displayio
from i2cdisplaybus import I2CDisplayBus  # NEW in CP10
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1106

# I2C on SCL=IO9, SDA=IO8
i2c = busio.I2C(scl=board.IO9, sda=board.IO8, frequency=400_000)

displayio.release_displays()

# Use I2CDisplayBus instead of displayio.I2CDisplay
display_bus = I2CDisplayBus(i2c, device_address=0x3C)

# 1.3" SH1106 is usually 128x64
display = adafruit_displayio_sh1106.SH1106(display_bus, width=128, height=64)

# Simple text
splash = displayio.Group()
display.root_group = splash
hello = label.Label(terminalio.FONT, text="Hello SH1106!", scale=2)
hello.anchor_point = (0.5, 0.5)
hello.anchored_position = (display.width // 2, display.height // 2)
splash.append(hello)
