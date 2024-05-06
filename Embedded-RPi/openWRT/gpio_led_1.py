from gpio4 import SysfsGPIO
from time import sleep


led = SysfsGPIO(27)
led.export = True
led.direction = "out"

for i in range(10):
    led.value = 1
    sleep(1)
    led.value = 0
    sleep(1)

led.export = False
