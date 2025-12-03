import time
import board
import digitalio
import usb_hid
import busio

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

import adafruit_as5600
import adafruit_mpr121

# -----------------------------
# HID Setup
# -----------------------------
keyboard = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

# -----------------------------
# Buttons (ESC = GP10, SPACE = GP11)
# -----------------------------
btn_esc = digitalio.DigitalInOut(board.GP10)
btn_esc.direction = digitalio.Direction.INPUT
btn_esc.pull = digitalio.Pull.UP

btn_space = digitalio.DigitalInOut(board.GP11)
btn_space.direction = digitalio.Direction.INPUT
btn_space.pull = digitalio.Pull.UP

prev_esc = True
prev_space = True

# -----------------------------
# I2C (AS5600 + MPR121 on GP0=SDA / GP1=SCL)
# -----------------------------
i2c = busio.I2C(board.GP1, board.GP0)

# AS5600
as5600 = adafruit_as5600.AS5600(i2c)
as5600.watchdog = 0
as5600.power_mode = 0

# MPR121
print("Initializing MPR121...")
try:
    mpr121 = adafruit_mpr121.MPR121(i2c)
    print("MPR121 detected!")
except Exception as e:
    print("ERROR: Could not initialize MPR121.")
    print("Reason:", e)
    while True:
        time.sleep(1)

# -----------------------------
# SAFE MPR121 SENSITIVITY PATCH
# -----------------------------
TOUCH_THRESHOLD = 30
RELEASE_THRESHOLD = 6

try:
    # Wait for MPR121 to fully come online
    time.sleep(0.05)

    # Apply thresholds safely
    mpr121.set_thresholds(TOUCH_THRESHOLD, RELEASE_THRESHOLD)
    print("MPR121 thresholds applied.")

except Exception as e:
    print("Warning: Could not set thresholds:", e)

# -----------------------------
# Mouse Motion Setup
# -----------------------------
last_angle = as5600.angle
SENSITIVITY = 0.7
mouse_down = False

print("All devices initialized.")
time.sleep(0.5)

# -----------------------------
# Main Loop
# -----------------------------
while True:

    # -------- BUTTON HANDLING --------
    esc_state = btn_esc.value
    space_state = btn_space.value

    if esc_state != prev_esc:
        if not esc_state:
            keyboard.press(Keycode.ESCAPE)
            print("ESC PRESSED")
        else:
            keyboard.release(Keycode.ESCAPE)
            print("ESC RELEASED")
        prev_esc = esc_state

    if space_state != prev_space:
        if not space_state:
            keyboard.press(Keycode.SPACE)
            print("SPACE PRESSED")
        else:
            keyboard.release(Keycode.SPACE)
            print("SPACE RELEASED")
        prev_space = space_state

    # -------- AS5600 ENCODER → MOUSE X --------
    angle = as5600.angle
    delta = angle - last_angle

    if delta > 2048:
        delta -= 4096
    elif delta < -2048:
        delta += 4096

    last_angle = angle
    move_x = int(delta * SENSITIVITY)

    if move_x != 0:
        mouse.move(x=move_x)

    # -------- MPR121 DEBUGGING --------
    touched = []
    for i in range(12):
        if mpr121[i].value:
            touched.append(i)

    if touched:
        print("Touched pads:", touched)

    # Left click logic
    if touched and not mouse_down:
        print("MOUSE LEFT CLICK DOWN")
        mouse.press(Mouse.LEFT_BUTTON)
        mouse_down = True

    if not touched and mouse_down:
        print("MOUSE LEFT CLICK UP")
        mouse.release(Mouse.LEFT_BUTTON)
        mouse_down = False

    time.sleep(0.01)
