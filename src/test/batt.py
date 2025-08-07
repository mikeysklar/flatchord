import time
import board
import digitalio

# --- Enable peripheral power (for battery mode) ---
vcc = digitalio.DigitalInOut(board.VCC_OFF)
vcc.direction = digitalio.Direction.OUTPUT
vcc.value = True
time.sleep(0.5)  # Give peripherals time to power up

# --- Button Pin Map (nice!nano v2) ---
SW_PINS = [
    ("SW0", board.P1_04),
    ("SW1", board.P0_11),
    ("SW2", board.P1_00),
    ("SW3", board.P0_24),
    ("SW4", board.P1_06),
]

# Initialize buttons
buttons = []
for name, pin in SW_PINS:
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP
    buttons.append((name, b))

print("Button tester running. Press and hold any switch…")

# Main loop
while True:
    for name, b in buttons:
        if not b.value:  # LOW when pressed
            print(f"{name} pressed")
            time.sleep(0.2)  # simple debounce
    time.sleep(0.01)
