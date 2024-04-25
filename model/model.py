import os
import sys
from queue import Queue, Empty
from threading import Lock
from json import loads, JSONDecodeError
from datetime import datetime, timezone

# '2024-03-22T12:43:35.000Z'
# '2024-03-22T12:43:35.000+00:00'

try:
    from settings import Settings
    from wsjtx_db import WsjtxDb
    from utility import grid_square, timefromgps, todec, settimefromgps
    from event import ProcessID, Callback
    from tx_msg import heartbeat, reply, halt_tx, location
    from rx_msg import parse
except ModuleNotFoundError:
    from model.settings import Settings
    from model.wsjtx_db import WsjtxDb
    from model.utility import grid_square, timefromgps, todec, settimefromgps
    from model.event import ProcessID, Callback
    from model.tx_msg import heartbeat, reply, halt_tx, location
    from model.rx_msg import parse

APP_NAME = 'wsjtx-udp'

class _Model:
    def  __init__(self):
        self.get_platform()
        self.message = ''
        self.grid = None
        self.band = 0
        self.mode = None
        self.ordinal = 0
        self.de_call = ''
        self.update_time_request = False
        
        self.r = []
        self.calc_data_paths()
        self.settings = Settings(self.inin)
        self.wsjtx_db = WsjtxDb(self)
        self.lock = Lock()
        self.running = True
        self.queue = Queue()
        self._event_listeners = {}
        self.platform = self.get_platform()

    def get_platform(self):
        r = ''
        if os.name == 'nt':
            return 'win32'
        elif os.name == 'posix':
            if 'rpi' in os.uname().release:
                return 'rpi'
            else:
                return 'posix'
        return ''

    def calc_data_paths(self):
        # compute data folder in user local storage
        p = os.getenv('LOCALAPPDATA')
        if p is None:
            s = sys.path[0]
            p = os.path.split(s)
            if p[1] in ('controller','model','view'):
                p = p[0]
            else:
                p = s
            df = os.path.join(p, 'data')
        else:
            df = os.path.join(p, APP_NAME)
        if not os.path.exists(df):
            os.makedirs(df)

        self.dbn = os.path.join(df, APP_NAME + '.sqlite')
        self.adifn = os.path.join(df, APP_NAME + '.adi')
        self.inin = os.path.join(df, APP_NAME + '.ini')
        

    def notify_quit(self):
        self.running = False
        self.trigger_event(Callback.QUIT)
        self._event_listeners.clear()

    def notify_state(self, id_, open_):
        match id_:
            case ProcessID.GPS | ProcessID.GPS_SERIAL:
                self.trigger_event(Callback.GPS_OPEN, open_)
            case ProcessID.WSJTX:
                # print('WSJTX: %s' % ('open' if open_ else 'close'))
                pass
            

    def add_event_listener(self, event, fn):
        try:
            self._event_listeners[event].add(fn)
        except KeyError:
            self._event_listeners[event] = set({fn})

    def remove_event_listener(self, event, fn):
        try:
            self._event_listeners[event].remove(fn)
        except KeyError:
            pass

    def trigger_event(self, event, data=None):
        try:
            for fn in self._event_listeners[event]:
                fn(data)
        except KeyError:
            pass

    def save_main_window_position(self, x, y):
        self.settings.config['default']['main_x'] = str(x)
        self.settings.config['default']['main_y'] = str(y)

    @property
    def main_window_x(self):
        return int(self.settings.config['default']['main_x'])

    @main_window_x.setter
    def main_window_x(self, value):
        self.settings.config['default']['main_x'] = str(value)

    @property
    def main_window_y(self):
        return int(self.settings.config['default']['main_y'])

    @main_window_y.setter
    def main_window_y(self, value):
        self.settings.config['default']['main_y'] = str(value)

    @property
    def theme(self):
        return self.settings.config['default']['theme']

    @property
    def park(self):
        return self.settings.config['default']['park']

    @park.setter
    def park(self, value):
        self.settings.config['default']['park'] = value

    def do_call(self, msg):
        """ activate call in WSJT-X """
        self.trigger_event(Callback.WSJTX_SEND, reply(msg))

    def abort_tx(self):
        """ abort Tx in WSJT-X """
        self.trigger_event(Callback.WSJTX_SEND, halt_tx(True))
        self.trigger_event(Callback.WSJTX_SEND, halt_tx(False))

    def set_time(self):
        """ set current system time to GPS time """
        self.update_time_request = True

    @property
    def shift(self):
        return self.settings.config['default']['shift']

    @shift.setter
    def shift(self, value):
        self.settings.config['default']['shift'] = value

    def set_grid(self):
        """ set WSJT-X grid to GPS grid """
        if self.grid is not None:
            self.settings.grid = self.grid
            self.trigger_event(Callback.WSJTX_SEND, location(self.grid))

    def set_park(self, park):
        self.settings.config['default']['park'] = park

    def process(self, id_, data):
        match id_:
            case ProcessID.GPS:
                self.process_gps(data)
            case ProcessID.GPS_SERIAL:
                self.process_gps_serial(data)
            case ProcessID.WSJTX:
                self.process_wsjtx(data)

    def process_gps(self, data):
        for d in data.strip().split(b'\n'):
            try:
                j = loads(data)
                match j['class']:
                    case 'VERSION':
                        self.trigger_event(
                            Callback.GPS_SEND,
                            b'?WATCH={"enable":true,"json":true}')
                    case 'TPV':
                        if self.message > '':
                            self.trigger_event('gps_decode', self.message)
                            self.message = ''
                        else:
                            if 'lat' in j:
                                grid = grid_square(j['lon'], j['lat'])[:6]
                                self.grid = grid
                            else:
                                grid = None
                            if 'time' in j:
                                t = j['time']
                                if t.endswith('Z'):
                                    t = t[:-1] + '+00:00'
                                time = datetime.fromisoformat(t).time()
                            else:
                                time = None
                            self.trigger_event(
                                Callback.GPS_DECODE,
                                {'time': time, 'grid': grid})
            except JSONDecodeError:
                pass

    def process_gps_serial(self, data):
        a = data.decode().strip().split(',')
        match a[0]:
            case '$GPRMC':
                _, utc, _, la, la_dir, lo, lo_dir, _, _, dt = a[:10]
                tm = timefromgps(utc)
                lat = todec(la, la_dir)
                lon = todec(lo, lo_dir)
                grid = grid_square(lon,lat)
                if grid is None:
                    self.grid = None
                else:
                    self.grid = grid[:6]
                if self.update_time_request:
                    self.update_time_request = False
                    self.message = settimefromgps(dt, tm)
                if self.message > '':
                    self.trigger_event(
                        Callback.GPS_DECODE,
                        {'time': self.message, 'grid': self.grid})
                    self.message = ''
                else:
                    self.trigger_event(
                        Callback.GPS_DECODE,
                        {'time': f'{tm[0]:02d}:{tm[1]:02d}:{tm[2]:02d}',
                         'grid': self.grid})

    def process_decodes(self):
        if len(self.r) == 0:
            return
        pota = []
        cq = []
        call = []
        for i in self.r:
            dx_call = None
            msg_parse = i.message.split(' ')
            if msg_parse[0] == 'CQ':
                if msg_parse[1] == 'POTA':
                    dx_call = msg_parse[2]
                    append = pota
                else:
                    dx_call = msg_parse[1]
                    append = cq
            elif msg_parse[0] == self.de_call:
                dx_call = msg_parse[1]
                append = call
            else:
                continue
            if dx_call is not None:    
                if self.wsjtx_db.exists(dx_call, i) == 0:
                    append.append(i)                   
        pota.sort(key=lambda a: a.snr, reverse=True)
        call.sort(key=lambda a: a.snr, reverse=True)
        cq.sort(key=lambda a: a.snr, reverse=True)
        self.trigger_event(Callback.WSJTX_CALLS, (pota, call, cq))


    def update_status(self, d):
        self.band = d.dial_freq // 1_000_000
        n = datetime.now(timezone.utc)
        self.ordinal = n.toordinal()
        self.de_call = d.de_call.upper()
        if self.grid is None:
            self.grid = d.de_grid
        self.mode = d.mode


    def process_wsjtx(self, data):
        d = parse(data)
        msg_id = d.msg_id
        match msg_id:
            case 0:  # HEARTBEAT
                self.trigger_event(Callback.WSJTX_SEND, heartbeat())
            case 1:  # STATUS
                self.update_status(d)
                self.trigger_event(Callback.WSJTX_STATUS, d)
                if not d.decoding:
                    self.process_decodes()
                    self.r = []
            case 2:  # DECODE
                self.r.append(d)
            case 5:  # LOG
                self.wsjtx_db.add(d)
            case 12:  # ADIF
                self.wsjtx_db.add_log(d.text)

    @property
    def wsjtx_address(self):
        return (self.settings.config['default']['wsjtx_host'],
                int(self.settings.config['default']['wsjtx_port']))

    @property
    def gps_address(self):
        return (self.settings.config['rpi']['gps_host'],
                int(self.settings.config['rpi']['gps_port']))

    @property
    def gps_serial_address(self):
        return self.settings.config['win32']['gps_port']


    def close(self):
        self.running = False
        self.settings.save()
        self.wsjtx_db.close()
        # print('model closed')

model = _Model()
