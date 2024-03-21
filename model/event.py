from enum import Enum, auto

class ProcessID(Enum):
    MAIN = auto()
    GPS = auto()
    WSJTX = auto()

class Callback(Enum):
    QUIT = auto()
    GPS_SEND = auto()
    GPS_DECODE = auto()
    GPS_OPEN = auto()
    WSJTX_SEND = auto()
    WSJTX_OPEN = auto()
    WSJTX_STATUS = auto()
    WSJTX_CALLS = auto()

