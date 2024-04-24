from enum import Enum, auto

class ProcessID(Enum):
    MAIN = auto()
    GPS = auto()
    GPS_SERIAL = auto()
    WSJTX = auto()

class Callback(Enum):
    QUIT = auto()
    GPS_SEND = auto()
    GPS_DECODE = auto()
    GPS_OPEN = auto()
    GPS_SERIAL_SEND = auto()
    GPS_SERIAL_DECODE = auto()
    GPS_SERIAL_OPEN = auto()
    WSJTX_SEND = auto()
    WSJTX_OPEN = auto()
    WSJTX_STATUS = auto()
    WSJTX_CALLS = auto()

