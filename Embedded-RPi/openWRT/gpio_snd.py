from gpio4 import SysfsGPIO
from time import sleep

buzzer = SysfsGPIO(23)
buzzer.export = True
buzzer.direction = "out"

frequencies = [33,
               35,
               37,
               39,
               41,
               44,
               46,
               49,
               52,
               55,
               58,
               62,
               65,
               69,
               73,
               78,
               82,
               87,
               93,
               98,
               104,
               110,
               117,
               123]


def calculate_state_times(frequency, duty_cycle):
    if frequency == 0:
        period = 0
    else:
        period = 1/frequency
    high_state_time = duty_cycle * period / 100
    low_state_time = period - high_state_time
    return (high_state_time, low_state_time)


def pwm_alternating_frequency(duty_cycle):
    if duty_cycle > 100 or duty_cycle < 0:
        raise ValueError

    for frequency in frequencies:
        high_state_time, low_state_time = calculate_state_times(
            frequency, duty_cycle)

        buzzer.value = 1

        sleep(high_state_time)

        buzzer.value = 0
        sleep(low_state_time)


pwm_alternating_frequency(50)

buzzer.export = False
