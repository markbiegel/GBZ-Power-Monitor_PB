#!/usr/bin/env python2.7
# date: 30/05/16
# author: Popcorn <abandonedemails@gmail.com> - Add "Sudomod" in the subject or your message will not be received
# version: 1.0a
# name: GBZ-Power-Monitor - a Power Management utility for the Gameboy Zero project
# description: a GPIO monitor that detects low battery and power switch status which provides a graceful shutdown facility
# source: https://github.com/Camble/GBZ-Power-Monitor_PB

import RPi.GPIO as GPIO
import os
import sys
import time

batteryGPIO    = 17  # GPIO 17/pin 0
powerGPIO      = 27  # GPIO 27/pin 2
redLEDGPIO     = 21   # GPIO 23 /pin 16
greenLEDGPIO   = 20   # GPIO 24 /pin 18
sampleRate     = 0.1 # tenth of a second
batteryTimeout = 10  # 10 seconds
powerTimeout   = 1   # 1 second
shutdownVideo  = "~/GBZ-Power-Monitor_PB/lowbattshutdown.mp4" # use no space or non-alphanum characters
lowalertVideo  = "~/GBZ-Power-Monitor_PB/lowbattalert.mp4"    # use no space or non-alphanum characters
playerFlag     = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(batteryGPIO, GPIO.IN) # No pull_up_down for LBO with voltage clamped with diode
GPIO.setup(powerGPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(redLEDGPIO, GPIO.OUT)
GPIO.setup(greenLEDGPIO, GPIO.OUT)

def lowBattery(channel):
  #Checking for LED bounce for the duration of the battery Timeout
  for bounceSample in range(1, int(round(batteryTimeout / sampleRate))):
    time.sleep(sampleRate)
    #green_constant()

    if GPIO.input(batteryGPIO) is 1:
       break

  global playerFlag
  while playerFlag is 1:
    time.sleep(1)

  #If the LED is a solid condition, there will be no bounce.  Launch shutdown video and then gracefully shutdown
  if bounceSample is int(round(batteryTimeout / sampleRate)) - 1:
    playerFlag = 1
    os.system("/usr/bin/omxplayer --no-osd --layer 999999 " + shutdownVideo + " --alpha 180;")
    if GPIO.input(batteryGPIO) is 0:
      os.system("sudo shutdown -h now")
      playerFlag = 0
      sys.exit(0)

  #If the LED is a solid for more than 10% of the timeout, we know that the battery is getting low.  Launch the Low Battery alert.
  if bounceSample > int(round(batteryTimeout / sampleRate * 0.1)):
    playerFlag = 1
    os.system("/usr/bin/omxplayer --no-osd --layer 999999 " + lowalertVideo + " --alpha 160;")
    playerFlag = 0
    #red_blink_fast()

    #Discovered a bug with the Python GPIO library and threaded events.  Need to unbind and rebind after a System Call or the program will crash
    GPIO.remove_event_detect(batteryGPIO)
    GPIO.add_event_detect(batteryGPIO, GPIO.BOTH, callback=lowBattery, bouncetime=300)

    #If we know the battery is low, we aggresively monitor the level to ensure we shutdown once the Power Timeout is exceeded.
    lowBattery(batteryGPIO)

def powerSwitch(channel):
  #Checking for LED bounce for the duration of the Power Timeout
  for bounceSample in range(1, int(round(powerTimeout / sampleRate))):
    time.sleep(sampleRate)
    if GPIO.input(powerGPIO) is 1:
       break

  if bounceSample is int(round(powerTimeout / sampleRate)) - 1:
      #When the Power Switch is placed in the off position with no bounce for the duration of the Power Timeout, we immediately shutdown
      #GPIO.output(greenLEDGPIO, GPIO.HIGH)
      green_flash()
      os.system("sudo shutdown -h now")
      
      #GPIO.output(greenLEDGPIO, GPIO.HIGH)
      #GPIO.output(redLEDGPIO, GPIO.HIGH)
      try:
         sys.stdout.close()
      except:
         pass
      try:
         sys.stderr.close()
      except:
         pass

      sys.exit(0)

def green_flash():
    blink_time_on  = 0.5
    blink_time_off = 0.5
    leds = 0
    update_leds(leds, blink_time_on, blink_time_off)

def yellow_blink_fast():
    blink_time_on  = 0.5
    blink_time_off = 0.5
    leds = 3
    update_leds(leds, blink_time_on, blink_time_off)

def green_constant():
    blink_time_on  = 0
    blink_time_off = 0
    leds = 1
    update_leds(leds, blink_time_on, blink_time_off)

def yellow_constant():
    blink_time_on  = 0
    blink_time_off = 0
    leds = 2
    update_leds(leds, blink_time_on, blink_time_off)

def update_leds(current_leds, time_on, time_off):
    global led_pin
    global led_states
    global poll_interval
    poll_interval = 30
    if time_off == 0:
        # constant on
        if leds == 2:
          GPIO.output(redLEDGPIO, GPIO.LOW)
        #GPIO.output(greenLEDGPIO, GPIO.LOW)
        time.sleep(poll_interval)
    else:
        # blink
        n_cycles = int(float(poll_interval) / float(time_on + time_off))
        for i in range(n_cycles):
            # led on, sleep, led off, sleep
            #if leds == 3:
            #  GPIO.output(greenLEDGPIO, GPIO.LOW)
            GPIO.output(greenLEDGPIO, GPIO.LOW)
            time.sleep(time_on)
            #if leds == 3:
            #  GPIO.output(greenLEDGPIO, GPIO.HIGH)
            GPIO.output(greenLEDGPIO, GPIO.HIGH)
            time.sleep(time_off)

def main():
  GPIO.output(greenLEDGPIO, GPIO.LOW)
  #green_flash()
  #if the Low Battery LED is active when the program launches, handle it
  if GPIO.input(batteryGPIO) is 0:
    lowBattery(batteryGPIO)

  #if the Power Switch is active when the program launches, handle it
  if GPIO.input(powerGPIO) is 0:
    powerSwitch(powerGPIO)

  #Add threaded event listeners for the Low Battery and Power Switch
  try:
    GPIO.remove_event_detect(batteryGPIO)
    GPIO.add_event_detect(batteryGPIO, GPIO.FALLING, callback=lowBattery, bouncetime=300)

    GPIO.remove_event_detect(powerGPIO)
    GPIO.add_event_detect(powerGPIO, GPIO.FALLING, callback=powerSwitch, bouncetime=300)
  except KeyboardInterrupt:
    GPIO.cleanup()

main()

#We make an endless loop so the threads running the GPIO events will always be listening, in the future we can add Battery Level monitoring here
while True:
  time.sleep(1)

GPIO.cleanup()
