import time
import board
import busio
import digitalio
import adafruit_ssd1306

# Power enable for battery mode
vcc = digitalio.DigitalInOut(board.VCC_OFF)
vcc.direction = digitalio.Direction.OUTPUT
vcc.value = True
time.sleep(0.5)

# I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# OLED setup
reset_pin = None  # or set to a digitalio.DigitalInOut pin if you're using RESET
#oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, reset=reset_pin)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
oled.text("OLED Ready!", 0, 0, 1)
oled.show()

# Button setup
SW_PINS = [
    ("SW0", board.P1_04),
    ("SW1", board.P0_11),
    ("SW2", board.P1_00),
    ("SW3", board.P0_24),
    ("SW4", board.P1_06),
]

buttons = []
for name, pin in SW_PINS:
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP
    buttons.append((name, b))

# Main loop
while True:
    for name, b in buttons:
        if not b.value:
            print(f"{name} pressed")
            oled.fill(0)
            oled.text(f"{name} pressed", 0, 0, 1)
            oled.show()
            time.sleep(0.2)
    time.sleep(0.01)
