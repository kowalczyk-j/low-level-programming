#!/usr/bin/env python3
from ev3dev2.motor import (
    LargeMotor,
    MediumMotor,
    OUTPUT_A,
    OUTPUT_B,
    OUTPUT_C,
    SpeedPercent,
    MoveTank,
)
from ev3dev2.sensor.lego import ColorSensor, InfraredSensor
from ev3dev2.button import Button
from time import sleep
from enum import Enum

KP = 4  # Wzmocnienie proporcjonalne 4
KI = 0.01  # Wzmocnienie całkowe 0.15
KD = 1  # Wzmocnienie różniczkowe 1
PID_SCALE = 100
DEFAULT_SPEED = 10
MAX_SPEED = DEFAULT_SPEED + 40  # Maksymalna prędkość silników
SLEEP_AFTER_MODE_CHANGE = 0.025

# Inicjalizacja silników, czujników i przycisku
tank_drive = MoveTank(OUTPUT_A, OUTPUT_B)
medium_motor = MediumMotor(OUTPUT_C)
left_color_sensor = ColorSensor("in2")
right_color_sensor = ColorSensor("in1")
ir_sensor = InfraredSensor("in3")
button = Button()

def calibrate():
    left_color_sensor.calibrate_white()
    right_color_sensor.calibrate_white()
    sleep(SLEEP_AFTER_MODE_CHANGE)
    left_intensity = left_color_sensor.reflected_light_intensity
    right_intensity = right_color_sensor.reflected_light_intensity
    print("left = " + str(left_intensity))
    print("right = " + str(right_intensity))
    offset = (left_intensity - right_intensity) / 2
    return -offset, offset

def calculate_pid(last_error=0, integral=0, left_offset=0, right_offset=0):
    left_intensity = left_color_sensor.reflected_light_intensity + left_offset
    right_intensity = right_color_sensor.reflected_light_intensity + right_offset
    error = (left_intensity - right_intensity) / 2
    integral = integral + error
    derivative = error - last_error
    steer_value = KP * error + KI * integral + KD * derivative

    return last_error, integral, steer_value

def follow_line(last_error=0, integral=0):
    left_color_sensor.mode = ColorSensor.MODE_COL_REFLECT
    right_color_sensor.mode = ColorSensor.MODE_COL_REFLECT
    sleep(SLEEP_AFTER_MODE_CHANGE)
    last_error, integral, pid_output = calculate_pid(
        last_error, integral, left_offset, right_offset)
    pid_scaled = pid_output * DEFAULT_SPEED / PID_SCALE
    left_speed = max(min(DEFAULT_SPEED - pid_scaled, MAX_SPEED), -MAX_SPEED)
    right_speed = max(min(DEFAULT_SPEED + pid_scaled, MAX_SPEED), -MAX_SPEED)

    tank_drive.on(left_speed, right_speed)  # Jazda prosto
    return last_error, integral


if __name__ == "__main__":
    print("Starting calibration...")
    left_offset, right_offset = calibrate()
    print("Calibration completed...")
    while True:
        follow_line()

