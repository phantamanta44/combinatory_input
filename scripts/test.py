#!/usr/bin/env python

from std_msgs.msg import Float32
from combinatory_processing import spin
from combinatory_input import find_joysticks

def main():
    device = find_joysticks().with_axes_gte(2).with_buttons_gte(4).find_any()
    with device.open_joydev() as controller:
        magn_x = controller.axis(0)
        magn_y = controller.axis(1)
        spin('joy_magn', [
            magn_x.join(magn_y, lambda x, y: (x*x + y*y)**0.5).map(Float32).sink('joy_magn', Float32)
        ])

if __name__ == '__main__':
    main()
