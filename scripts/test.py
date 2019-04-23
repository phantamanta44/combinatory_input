#!/usr/bin/env python

from combinatory_input import gamepad, codes
from combinatory_processing import spin
from std_msgs.msg import Float32

if __name__ == '__main__':
    with gamepad() as controller:
        magn_x = controller.axis(codes.axis.ABS_X)
        magn_y = controller.axis(codes.axis.ABS_Y)
        spin('joy_magn', [
            magn_x.join(magn_y, lambda x, y: (x**2 + y**2)**0.5).map(Float32).sink('joy_magn', Float32)
        ])
