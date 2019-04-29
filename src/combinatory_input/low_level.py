class ImpulseBuffer:
    def __init__(self, width):
        self.buffer = bytearray([0]) * width
        self.width = width
        self.pointer = 0

    def remaining(self):
        return self.width - self.pointer

    def write(self, data):
        if data:
            for datum in data:
                self.buffer[self.pointer] = datum
                self.pointer += 1

    def is_ready(self):
        return self.pointer >= self.width

    def read(self):
        self.pointer = 0
        return self.buffer
