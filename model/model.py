import os
import sys
from queue import Queue, Empty
from threading import Lock
from json import loads, JSONDecodeError
from datetime import datetime, timezone

try:
    from settings import Settings
    from wsjtx_db import WsjtxDb
    from utility import grid_square
    from event import ProcessID, Callback
    from tx_msg import heartbeat, reply, halt_tx, location
    from rx_msg import parse
except ModuleNotFoundError:
    from model.settings import Settings
    from model.wsjtx_db import WsjtxDb
    from model.utility import grid_square
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
            df = os.path.join(l, APP_NAME)
        if not os.path.exists(df):
            os.makedirs(df)

        self.dbn = os.path.join(df, APP_NAME + '.sqlite')
        self.adifn = os.path.join(df, APP_NAME + '.adi')
        self.inin = os.path.join(df, APP_NAME + '.ini')
        

    def notify_quit(self):
        self.trigger_event(Callback.QUIT)

    def notify_state(self, id_, open_):
        match id_:
            case ProcessID.GPS:
                self.trigger_event(Callback.GPS_OPEN, open_)
            case ProcessID.WSJTX:
                pass
                # print('WSJTX: %s' % ('open' if open_ else 'close'))
            

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
        pass

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
                                time = datetime.fromisoformat(j['time']).time()
                            else:
                                time = None
                            self.trigger_event(
                                Callback.GPS_DECODE,
                                {'time': time, 'grid': grid})
            except JSONDecodeError:
                pass

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
        if self.platform in ('rpi','posix'):
            return (self.settings.config['rpi']['gps_host'],
                    int(self.settings.config['rpi']['gps_port']))
        else:
            return self.settings.config['win32']['gps_port']



    def close(self):
        self.running = False
        self.settings.save()
        self.wsjtx_db.close()

model = _Model()
