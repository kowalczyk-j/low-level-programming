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

class Color(Enum):
    RED = [242, 41, 25]
    BLUE = [42, 119, 235]
    GREEN = [36, 150, 97]
    WHITE = [255, 255, 255]
    BLACK = [34, 36, 28]
    YELLOW = [255, 255, 60]

COLOR_PICK_UP = Color.RED.value
COLOR_DROP_OFF = Color.BLUE.value

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


def rotate_180deg():
    tank_drive.on_for_rotations(SpeedPercent(10), SpeedPercent(-10), 1.1)


def turn_left():
    # Ze względu na odległość czujników od kół podjedź prosto przed skrętem
    tank_drive.on_for_rotations(SpeedPercent(10), SpeedPercent(10), 0.3)
    tank_drive.on_for_rotations(SpeedPercent(10), SpeedPercent(-10), 0.6)


def turn_right():
    # Ze względu na odległość czujników od kół podjedź prosto przed skrętem
    tank_drive.on_for_rotations(SpeedPercent(10), SpeedPercent(10), 0.3)
    tank_drive.on_for_rotations(SpeedPercent(-10), SpeedPercent(10), 0.6)


def check_color(target_color):
    left_color_sensor.mode = ColorSensor.MODE_COL_COLOR
    right_color_sensor.mode = ColorSensor.MODE_COL_COLOR
    sleep(SLEEP_AFTER_MODE_CHANGE)
    left_rgb = left_color_sensor.rgb
    right_rgb = right_color_sensor.rgb
    left_within_range = all(abs(left_rgb[i] - target_color[i]) <= 20 for i in range(3))
    right_within_range = all(abs(right_rgb[i] - target_color[i]) <= 20 for i in range(3))
    return left_within_range, right_within_range


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


# STAN 1
def follow_line_to_turn_and_pick_up(last_error=0, integral=0):
    print("STAN 1")
    while True:
        last_error, integral = follow_line(last_error, integral)
        left_color, right_color = check_color(COLOR_PICK_UP)
        if left_color:
            turn_left()
            follow_line_to_pick_up(last_error, integral)
            return
        if right_color:
            turn_right()
            follow_line_to_pick_up(last_error, integral)
            return


# STAN 2
def follow_line_to_pick_up(last_error=0, integral=0):
    print("STAN 2")
    while True:
        last_error, integral = follow_line(last_error, integral)
        left_color, right_color = check_color(COLOR_PICK_UP)
        if left_color and right_color:
            pick_up(last_error, integral)
            return


# STAN 3
def pick_up(last_error=0, integral=0, sensor_distance=0.1):
    print("STAN 3")
    while True:
        tank_drive.on(10, 10)
        if ir_sensor.proximity < sensor_distance:
            tank_drive.on_for_rotations(SpeedPercent(10), SpeedPercent(10), 0.2)
            tank_drive.off()
            sleep(0.5)
            medium_motor.on_for_degrees(SpeedPercent(50), 300)  # Podnieś ramię
            sleep(0.5)
            rotate_180deg()
            tank_drive.on_for_seconds(
                SpeedPercent(10), SpeedPercent(10), 1
            )
            follow_line_from_pick_up(last_error, integral)
            return


# STAN 4
def follow_line_from_pick_up(last_error=0, integral=0):
    print("STAN 4")
    while True:
        last_error, integral = follow_line(last_error, integral)
        left_color, right_color = check_color(Color.BLACK.value)
        if (left_color and right_color):
            turn_right()
            follow_line_to_turn_and_drop_off()
            return


# STAN 5
def follow_line_to_turn_and_drop_off(last_error=0, integral=0):
    print("STAN 5")
    while True:
        last_error, integral = follow_line(last_error, integral)
        left_color, right_color = check_color(COLOR_DROP_OFF)
        if left_color:
            turn_left()
            follow_line_to_drop_off(last_error, integral)
            return
        if right_color:
            turn_right()
            follow_line_to_drop_off(last_error, integral)
            return


# STAN 6
def follow_line_to_drop_off(last_error=0, integral=0):
    print("STAN 6")
    while True:
        last_error, integral = follow_line(last_error, integral)
        left_color, right_color = check_color(COLOR_DROP_OFF)
        if left_color and right_color:
            drop_off()
            return


# STAN 7
def drop_off():
    print("STAN 7")
    tank_drive.off()
    sleep(0.5)
    medium_motor.on_for_degrees(SpeedPercent(50), -300)  # Opuść ramię
    sleep(0.5)
    tank_drive.on_for_seconds(SpeedPercent(-10), SpeedPercent(-10), 1)  # Wycofaj


if __name__ == "__main__":
    print("Starting calibration...")
    left_offset, right_offset = calibrate()
    print("Calibration completed...")
    follow_line_to_turn_and_pick_up()
