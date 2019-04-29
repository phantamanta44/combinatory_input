import os
import os_call
from .hid import device_joydev

NAME_BUF_LEN = 128

class Finder():
    def __init__(self, initial_set):
        self.possible = initial_set
        self.predicates = []

    def filter(self, predicate):
        self.predicates.append(predicate)
        return self

    def name_contains(self, text):
        return self.filter(lambda k: text in k.name)

    def with_buttons_eq(self, count):
        return self.filter(lambda k: k.btn_count == count)

    def with_buttons_gte(self, count):
        return self.filter(lambda k: k.btn_count >= count)

    def with_buttons_lte(self, count):
        return self.filter(lambda k: k.btn_count <= count)

    def with_axes_eq(self, count):
        return self.filter(lambda k: k.axis_count == count)

    def with_axes_gte(self, count):
        return self.filter(lambda k: k.axis_count >= count)

    def with_axes_lte(self, count):
        return self.filter(lambda k: k.axis_count <= count)

    def find_all(self):
        results = []
        def matches(dev_desc):
            for predicate in self.predicates:
                if not predicate(dev_desc):
                    return False
            return True
        for device_file in self.possible:
            with open(device_file, 'rb') as device:
                file_desc = device.fileno()
                name = os_call.ioctl_str(file_desc, os_call.JSIOCGNAME(NAME_BUF_LEN), NAME_BUF_LEN)
                btn_count = os_call.ioctl_byte(file_desc, os_call.JSIOCGBUTTONS)
                axis_count = os_call.ioctl_byte(file_desc, os_call.JSIOCGAXES)
                dev_desc = DeviceDescriptor(device_file, name, btn_count, axis_count)
                if matches(dev_desc):
                    results.append(dev_desc)
        return results

    def find_any(self):
        all_results = self.find_all()
        if not all_results:
            raise ValueError('No joysticks found matching criteria!')
        return all_results[0]

class DeviceDescriptor:
    def __init__(self, device_file, name, btn_count, axis_count):
        self.device_file = device_file
        self.name = name
        self.btn_count = btn_count
        self.axis_count = axis_count

    def open_joydev(self, debug=False):
        return device_joydev(self.device_file, self.name, debug)

def find_joysticks():
    return Finder(['/dev/input/by-id/' + dev for dev in os.listdir('/dev/input/by-id') \
        if dev.endswith('-joystick') and not dev.endswith('-event-joystick')])
