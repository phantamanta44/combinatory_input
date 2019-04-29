import fcntl
import os
import io
import threading
from struct import unpack
from combinatory_processing import source_poll
from .low_level import ImpulseBuffer

INITIAL_VALUES = {
    'axis': 0,
    'flag': False
}

class StateRegister:
    def __init__(self, input_type):
        self.state = INITIAL_VALUES[input_type]
        self.reg_lock = threading.RLock()

    def poll(self):
        with self.reg_lock:
            return self.state

    def write(self, state):
        with self.reg_lock:
            self.state = state

class HID:
    def __init__(self, input_device, name=None):
        self.dev = input_device
        self.name = name if name else str(type(input_device))
        self.state_lock = threading.RLock()
        self.state = {'axis': {}, 'flag': {}}

    def get_state_register(self, event_type, num):
        with self.state_lock:
            regs = self.state[event_type]
            if num in regs:
                return regs[num]
            reg = StateRegister(event_type)
            regs[num] = reg
            return reg

    def __enter__(self):
        self.dev.open_device(self)
        print 'Device initialized: ' + self.name
        return API(self)

    def __exit__(self, e_type, value, traceback):
        self.dev.close_device()

class API:
    def __init__(self, hid):
        self.hid = hid

    def axis(self, num):
        return source_poll(self.hid.get_state_register('axis', num).poll)

    def flag(self, num):
        return source_poll(self.hid.get_state_register('flag', num).poll)

EVENT_FORMAT = 'IhBB'

class InputDevice:
    def __init__(self, device_file, debug=False):
        self.device_file = device_file
        self.debug = debug
        self.stream = None
        self.thread_lock = threading.Lock()
        self.dead = False
        self.poll_thread = None

    def open_device(self, hid):
        self.stream = io.open(self.device_file, 'rb', 8)
        file_desc = self.stream.fileno()
        fcntl.fcntl(file_desc, fcntl.F_SETFL, fcntl.fcntl(file_desc, fcntl.F_GETFL) | os.O_NONBLOCK)
        read_buf = ImpulseBuffer(8)
        def poll():
            while True:
                if self.stream.readable():
                    read_buf.write(self.stream.read(read_buf.remaining()))
                    if read_buf.is_ready():
                        (_, value, event_type, control_id) = unpack(EVENT_FORMAT, read_buf.read())
                        if event_type == 0x02: # absolute axis
                            hid.get_state_register('axis', control_id).write(value)
                        elif event_type == 0x01: # button/key
                            hid.get_state_register('flag', control_id).write(value)
                        if self.debug:
                            print '%x: %d = %d' % (event_type, control_id, value)
                with self.thread_lock:
                    if self.dead:
                        break
        self.poll_thread = threading.Thread(target=poll)
        self.poll_thread.daemon = True
        self.poll_thread.start()

    def close_device(self):
        with self.thread_lock:
            self.dead = True
        self.poll_thread.join()

def device_joydev(device_file, name=None, debug=False):
    return HID(InputDevice(device_file, debug), name if name else device_file)
