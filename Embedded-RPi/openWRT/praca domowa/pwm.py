from time import sleep
from math import sin


def calculate_state_times(frequency, duty_cycle):
    if frequency == 0:
        period = 0
    else:
        period = 1/frequency
    high_state_time = duty_cycle * period / 100
    low_state_time = period - high_state_time
    return (high_state_time, low_state_time)


def pwm_alternating_frequency(frequency, duty_cycle, duration):
    if duty_cycle > 100 or duty_cycle < 0 or frequency <= 0:
        raise ValueError

    for cycle in range(duration):
        high_state_time, low_state_time = calculate_state_times(
            frequency, duty_cycle)
        print(
            f"Cycle #{cycle+1}\tf = {frequency}\tduty_cycle = {duty_cycle}\tt_h = {high_state_time}\tt_l = {low_state_time}")
        print("State: HIGH")
        sleep(high_state_time)

        print("State: LOW")
        sleep(low_state_time)

        frequency += abs(sin(cycle+1))


def pwm_alternating_duty(frequency, duty_cycle, duration):
    if duty_cycle > 100 or duty_cycle < 0 or frequency <= 0:
        raise ValueError

    ascending = True

    for cycle in range(duration):
        high_state_time, low_state_time = calculate_state_times(
            frequency, duty_cycle)
        print(
            f"Cycle #{cycle+1}\tf = {frequency}\tduty_cycle = {duty_cycle}\tt_h = {high_state_time}\tt_l = {low_state_time}")

        print("State: HIGH")
        sleep(high_state_time)

        print("State: LOW")
        sleep(low_state_time)

        if (duty_cycle + 10 * abs(sin(cycle+1))) >= 100:
            ascending = False

        if (duty_cycle - 10 * abs(sin(cycle+1))) <= 0:
            ascending = True

        if ascending:
            duty_cycle += 10 * abs(sin(cycle+1))
        else:
            duty_cycle -= 10 * abs(sin(cycle+1))

if __name__ == "__main__":
    print("PWM with alternating frequency:\n")
    pwm_alternating_frequency(0.5, 95, 5)
    print("PWM with alternating duty:\n")
    pwm_alternating_duty(0.5, 95, 5)

