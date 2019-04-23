from combinatory_processing import source_poll
from inputs import devices, iter_unpack
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
            data = self.dev._get_data(self.dev._get_total_read_size())
            if data:
                axis_updates = []
                flag_updates = []
                for (_, _, event_type, code, value) in iter_unpack(data):
                    if event_type == 0x03: # absolute axis
                        axis_updates.append((code, value))
                    elif event_type == 0x01: # button/key
                        flag_updates.append((code, value))
                if self.debug:
                    print('%x: %x = %d' % (event_type, code, value))
                with self.state_lock:
                    for update in axis_updates:
                        self._get_state_register('axis', update[0]).write(update[1])
                    for update in flag_updates:
                        self._get_state_register('flag', update[0]).write(update[1] == 1)
            with self.thread_lock:
                if self.dead:
                    break

    def __enter__(self):
        self.poll_thread.start()
        return API(self)

    def __exit__(self, e_type, value, traceback):
        with self.thread_lock:
            self.dead = True

class API:
    def __init__(self, hid):
        self.hid = hid

    def axis(self, num):
        return source_poll(self.hid._get_state_register('axis', num).poll)

    def flag(self, num):
        return source_poll(self.hid._get_state_register('flag', num).poll)

def gamepad(port=None, debug=False):
    if port is None:
        return HID(devices.gamepads[0], debug)
    for device in devices:
        if device.get_number() == port:
            return HID(device, debug)
    raise RuntimeError('Could not find gamepad on port ' + str(port))
