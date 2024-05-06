from gpio4 import SysfsGPIO
from time import sleep


button = SysfsGPIO(17)
button.export = True
button.direction = "in"

led = SysfsGPIO(27)
led.export = True
led.direction = "out"


while True:
    if button.value == 0:
        led.value = 1
        led.value = 0

led.export = False
button.export = False
