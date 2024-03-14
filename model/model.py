from queue import Queue, Empty
from threading import Lock
from json import loads, JSONDecodeError

try:
    from settings import Settings
    from wsjtx_db import WsjtxDb
    from utility import grid_square
except ModuleNotFoundError:
    from model.settings import Settings
    from model.wsjtx_db import WsjtxDb
    from model.utility import grid_square

class _Model:
    _MAIN_ID = 'main'
    _GPS_ID = 'gps'
    
    def  __init__(self):
        self.message = ''
        self.settings = Settings()
        self.wsjtx_db = WsjtxDb(self.settings.dbn, self.settings.adifn)
        self.lock = Lock()
        self.running = True
        self.queue = Queue()
        self._event_listeners = {}

    def notify_state(self, id_, open_):
        print(f'notify: {id_} open: {open_}\n')

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

    def trigger_event(self, event, data):
        try:
            for fn in self._event_listeners[event]:
                fn(data)
        except KeyError:
            pass

    def push(self, id_, data=None):
        if self.running:
            with self.lock:
                self.queue.put((id_, data))
                self.event_generate()

    def pop(self):
        if self.running:
            try:
                return self.queue.get_nowait()
            except Empty:
                pass

    def save_main_window_position(self, x, y):
        self.settings.config['default']['main_x'] = str(x)
        self.settings.config['default']['main_y'] = str(y)

    @property
    def main_window_setup(self):
        return (int(self.settings.config['default']['main_x']),
                int(self.settings.config['default']['main_y']),
                self.settings.config['default']['theme'])


    def do_call(self, msg):
        """ activate call in WSJT-X """
        pass

    def abort_tx(self):
        """ abort Tx in WSJT-X """
        pass

    def set_time(self):
        """ set current system time to GPS time """
        pass

    def set_grid(self):
        """ set WSJT-X grid to GPS grid """
        # wsjtx.send(location(grid))
        pass

    def process(self, id_, data):
        match id_:
            case _GPS_ID:
                self.process_gps(data)

    def process_gps(self, data):
        for d in data.strip().split(b'\n'):
            try:
                j = loads(data)
                match j['class']:
                    case 'VERSION':
                        self.trigger_event(
                            'gps_send',
                            b'?WATCH={"enable":true,"json":true}')
                    case 'TPV':
                        if self.message > '':
                            self.trigger_event('gps_decode', self.message)
                            self.message = ''
                        elif 'lat' in j:
                            grid = grid_square(j['lon'], j['lat'])[:6]
                        else:
                            grid = None
                        self.trigger_event(
                            'gps_decode',
                            {'time': None, 'grid': grid})
            except JSONDecodeError:
                pass


    def close(self):
        self.running = False
        self.settings.save()
        self.wsjtx_db.close()

model = _Model()
