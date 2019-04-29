import array
import fcntl

# somehow these constants work so whatever
JSIOCGAXES = 0x80016a11
JSIOCGBUTTONS = 0x80016a12

def JSIOCGNAME(length):
    return 0x80006a13 + (0x10000 * length)

def ioctl_str(file_desc, request, buf_length):
    buf = array.array('c', ['\0'] * buf_length) # char[] initialized to nulls
    ioctl(file_desc, request, buf)
    return str(buf.tostring())

def ioctl_byte(file_desc, request):
    buf = array.array('B', [0]) # a single-uint8 buffer
    ioctl(file_desc, request, buf)
    return buf[0]

def ioctl(file_desc, request, buf):
    fcntl.ioctl(file_desc, request, buf)
