#!/usr/bin/env python3
import ev3dev2
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, SpeedPercent, MoveTank
from ev3dev2.sensor import INPUT_1, INPUT_2
from ev3dev2.sensor.lego import TouchSensor, ColorSensor, InfraredSensor
from ev3dev2.led import Leds
from ev3dev2.button import Button
from time import sleep

tank_drive = MoveTank(OUTPUT_A, OUTPUT_B)
left_color_sensor = ColorSensor('in2')
right_color_sensor = ColorSensor('in1')
button = Button()

SPEED = SpeedPercent(20) # prędkość podstawowa
TURN_SPEED = SpeedPercent(-10) # prędkość do skrętu koła
LIGHT_THRESHOLD = 50  # minimalna wartość jasności dla białego koloru

paused = False

def follow_line():
    global paused
    while True:
        if button.enter: # zatrzymanie robota
            paused = not paused
            if paused:
                tank_drive.off()
                print("Pausing...")
            else:
                print("Resuming...")
            sleep(0.5)
        
        if not paused:
            left_intensity = left_color_sensor.reflected_light_intensity
            right_intensity = right_color_sensor.reflected_light_intensity
            # Jeśli oba czujniki są na białym = czarna linia jest pomiędzy, jedź prosto
            if left_intensity > LIGHT_THRESHOLD and right_intensity > LIGHT_THRESHOLD:
                tank_drive.on(SPEED, SPEED)
            # Jeśli tylko lewy czujnik jest na białym = prawy czujnik wykryje czarny kolor, skręć w prawo
            elif left_intensity > LIGHT_THRESHOLD:
                tank_drive.on(TURN_SPEED, SPEED)
            # Jeśli tylko prawy czujnik jest na białym = lewy czujnik wykryje czarny kolor, skręć w lewo
            elif right_intensity > LIGHT_THRESHOLD:
                tank_drive.on(SPEED, TURN_SPEED)
            # Jeśli oba czujniki są poza białą planszą, zatrzymaj się
            else:
                tank_drive.on(SPEED, SPEED)
        sleep(0.1)  # Opóźnienie, aby uniknąć zbyt częstego odczytu

if __name__ == "__main__":
    print("Starting...")
    follow_line()
