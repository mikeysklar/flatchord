import time
import board
import digitalio

# Map buttons to SuperMini ESP32-S3 pins
SW_PINS = [
    ("SW0", board.IO7),
    ("SW1", board.IO6),
    ("SW2", board.IO5),
    ("SW3", board.IO4),
    ("SW4", board.IO2),
]

# Initialize inputs (wired: switch -> pin, other side -> GND)
buttons = []
for name, pin in SW_PINS:
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP   # internal pull-up; reads LOW when pressed
    buttons.append((name, b))

print("Button tester running. Press and hold any switch…")

# Main loop
while True:
    for name, b in buttons:
        if not b.value:          # LOW when pressed
            print(f"{name} pressed")
            time.sleep(0.2)      # simple debounce
    time.sleep(0.01)
