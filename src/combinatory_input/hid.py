from combinatory_processing import source_poll
from struct import unpack
import threading

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
    def __init__(self, input_device, debug=False):
        self.dev = input_device
        self.debug = debug
        self.state_lock = threading.RLock()
        self.state = {'axis': {}, 'flag': {}}
        self.thread_lock = threading.Lock()
        self.dead = False
        self.poll_thread = threading.Thread(target=self._poll)
        self.poll_thread.daemon = True

    def _get_state_register(self, event_type, num):
        with self.state_lock:
            regs = self.state[event_type]
            if num in regs:
                return regs[num]
            else:
                reg = StateRegister(event_type)
                regs[num] = reg
                return reg

    def _poll(self):
        while True:
            with self.state_lock:
                (_, value, event_type, control_id) = self.dev.read_event()
                if event_type == 0x03: # absolute axis
                    self._get_state_register('axis', control_id).write(value)
                elif event_type == 0x01: # button/key
                    self._get_state_register('flag', control_id).write(value)
                if self.debug:
                    print('%x: %d = %d' % (event_type, control_id, value))
            with self.thread_lock:
                if self.dead:
                    break

    def __enter__(self):
        self.dev.open_device()
        self.poll_thread.start()
        return API(self)

    def __exit__(self, e_type, value, traceback):
        with self.state_lock:
            try:
                self.dev.close_device()
            except IOError:
                pass
        with self.thread_lock:
            self.dead = True

class API:
    def __init__(self, hid):
        self.hid = hid

    def axis(self, num):
        return source_poll(self.hid._get_state_register('axis', num).poll)

    def flag(self, num):
        return source_poll(self.hid._get_state_register('flag', num).poll)

def gamepad(device_file=None, debug=False):
    return HID(InputDevice(device_file), debug)

EVENT_FORMAT = 'IhBB'

class InputDevice:
    def __init__(self, device_file):
        self.device_file = device_file
        self.file_handle = None

    def read_event(self):
        return unpack(EVENT_FORMAT, self.file_handle.read(8))

    def open_device(self):
        self.file_handle = open(self.device_file, 'r')
        self.file_handle.read(192) # ignore header
        print 'Device initialized: ' + self.device_file

    def close_device(self):
        self.file_handle.close()
