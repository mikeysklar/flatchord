import board, busio

# Explicitly define I2C pins: SCL = GPIO9, SDA = GPIO8
i2c = busio.I2C(scl=board.IO9, sda=board.IO8)

# Test scan
while not i2c.try_lock():
    pass
try:
    print("I2C addresses found:", [hex(x) for x in i2c.scan()])
finally:
    i2c.unlock()
