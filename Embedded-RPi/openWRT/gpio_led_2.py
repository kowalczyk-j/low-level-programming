from gpio4 import SysfsGPIO
from time import sleep
from math import sin


led = SysfsGPIO(27)
led.export = True
led.direction = "out"


def calculate_state_times(frequency, duty_cycle):
    if frequency == 0:
        period = 0
    else:
        period = 1/frequency
    high_state_time = duty_cycle * period / 100
    low_state_time = period - high_state_time
    return (high_state_time, low_state_time)


def pwm_alternating_duty(frequency, duty_cycle, duration):
    if duty_cycle > 100 or duty_cycle < 0 or frequency <= 0:
        raise ValueError

    ascending = True

    for cycle in range(duration):
        high_state_time, low_state_time = calculate_state_times(
            frequency, duty_cycle)

        led.value = 1
        sleep(high_state_time)

        led.value = 0
        sleep(low_state_time)

        if (duty_cycle + 10 * abs(sin(cycle+1))) >= 100:
            ascending = False

        if (duty_cycle - 10 * abs(sin(cycle+1))) <= 0:
            ascending = True

        if ascending:
            duty_cycle += 10 * abs(sin(cycle+1))
        else:
            duty_cycle -= 10 * abs(sin(cycle+1))


pwm_alternating_duty(50, 0, 500)


led.export = False
