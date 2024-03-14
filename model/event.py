from enum import Enum, auto

class NotifyGUI(Enum):
    QUIT = auto()

    WSJTX_OPEN = auto()
    WSJTX_CLOSE = auto()
    WSJTX_HB = auto()
    WSJTX_CALLS = auto()
    WSJTX_STATUS = auto()
    
    GPS_OPEN = auto()
    GPS_CLOSE = auto()
    GPS_MSG = auto()
    GPS_DATA = auto()

