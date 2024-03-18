from queue import Queue, Empty
from threading import Lock
from json import loads, JSONDecodeError

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


class _Model:
    def  __init__(self):
        self.message = ''
        self.grid = None
        self.r = []
        self.settings = Settings()
        self.wsjtx_db = WsjtxDb(self.settings)
        self.lock = Lock()
        self.running = True
        self.queue = Queue()
        self._event_listeners = {}

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

    @property
    def platform(self):
        return self.settings.platform
        
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
                        elif 'lat' in j:
                            grid = grid_square(j['lon'], j['lat'])[:6]
                            self.grid = grid
                        else:
                            grid = None
                        self.trigger_event(
                            Callback.GPS_DECODE,
                            {'time': None, 'grid': grid})
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
            elif msg_parse[0] == self.settings.de_call:
                dx_call = msg_parse[1]
                append = call
            else:
                continue
            if dx_call is not None:    
                # if self.wsjtx_db.exists(dx_call, i) is None:
                    append.append(i)                   
        pota.sort(key=lambda a: a.snr, reverse=True)
        call.sort(key=lambda a: a.snr, reverse=True)
        cq.sort(key=lambda a: a.snr, reverse=True)
        self.trigger_event(Callback.WSJTX_CALLS, (pota, call, cq))


    def process_wsjtx(self, data):
        d = parse(data)
        msg_id = d.msg_id
        match msg_id:
            case 0:  # HEARTBEAT
                self.trigger_event(Callback.WSJTX_SEND, heartbeat())
            case 1:  # STATUS
                self.settings.update_status(d)
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
        

    def close(self):
        self.running = False
        self.settings.save()
        self.wsjtx_db.close()

model = _Model()
