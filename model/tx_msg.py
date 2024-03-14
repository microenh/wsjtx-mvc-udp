from struct import pack
from datetime import datetime, timezone


def qbool(d, x):
    d.append(pack('?', x))

def qint8(d, x):
    d.append(pack('b', x))

def quint8(d, x):
    d.append(pack('B', x))

def qint32(d, x):
    d.append(pack('>i', x))

def quint32(d, x):
    d.append(pack('>I', x))

def qint64(d, x):
    d.append(pack('>q', x))

def quint64(d, x):
    d.append(pack('>Q', x))
    
def qdouble(d, x):
    d.append(pack('>d', x))

def qdatetime(d, x):
    jday = x.toordinal() + 1721325
    msec = x.hour * 3600_000 + x.minute * 60_000 + x.second * 1_000 + x.microsecond // 1_000

    if x.tzinfo is None:
        # naive - assume local
        timespec = 0
    elif x.tzinfo == timezone.utc:
        timespec = 1
    elif x.tzname()[:3] == 'UTC':
        # offset
        timespec = 2
    else:
        # assume local
        timespec = 0
        
    quint64(d, jday)
    quint32(d, msec)
    quint8(d, timespec)
    if timespec == 2:
        quint32(d, x.utcoffset().total_seconds())

def qcolor(d, color=None):
    """
    color = (A,R,G,B)
    """
    FMT = '>BHHHHH'
    if color is None:
        d.append(pack(FMT, 0,0,0,0,0,0))
    else:
        d.append(pack(FMT, 1, *color, 0))

def qutf8(d, x):
    qint32(d, len(x))
    d.append(x.encode())


def header(d, msg_id):
    MAGIC = 0xadbccbda
    SCHEMA = 2
    APP_ID = 'WSJT-X'
    quint32(d, MAGIC)
    quint32(d, SCHEMA)
    quint32(d, msg_id)
    qutf8(d, APP_ID)

def heartbeat():
    d = []
    MAX_SCHEMA = 3
    VERSION = '1.0.0'
    REVISION = '00001'
    header(d, 0)
    quint32(d, MAX_SCHEMA)
    qutf8(d, VERSION)
    qutf8(d, REVISION)
    return b''.join(d)

def clear(window=0):
    d = []
    header(d, 3);
    quint8(d, window)
    return b''.join(d)

def reply(msg, modifiers=0):
    d = []
    header(d, 4)
    quint32(d, msg.time)
    qint32(d, msg.snr)
    qdouble(d, msg.delta_time)
    quint32(d, msg.delta_freq)
    qutf8(d, msg.mode)
    qutf8(d, msg.message)
    qbool(d, msg.low_conf)
    quint8(d, modifiers)
    return b''.join(d)

def close():
    d = []
    header(d, 6)
    return b''.join(d)

def replay():
    d = []
    header(d, 7)
    return b''.join(d)

def halt_tx(auto_tx_only=False):
    d = []
    header(d, 8)
    qbool(d, auto_tx_only)
    return b''.join(d)

def free_text(text, send):
    d = []
    header(d, 9)
    qutf8(d, text)
    qbool(d, send)
    return b''.join(d)

def location(location):
    d = []
    header(d, 11)
    qutf8(d, location)
    return b''.join(d)


def highlight_call(call,
                   foreground=None,
                   background=(0xffff,0,0,0),
                   highlight_last=True):
    d = []
    header(d,13)
    qutf8(d, call)
    qcolor(d, background)
    qcolor(d, foreground)
    qbool(d, highlight_last)
    return b''.join(d)
