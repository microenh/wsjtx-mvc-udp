from model.model import model
from model.event import ProcessID, Callback 
from view.main import MainView

try:
    from udp_client import UDPClientController
    from udp_server import UDPServerController
    from gps_serial import GPSSerial
except ModuleNotFoundError:
    from controller.udp_client import UDPClientController
    from controller.udp_server import UDPServerController
    from controller.gps_serial import GPSSerial

class MainController:
    def __init__(self, id_):
        self.id_ = id_
        self.win32 = model.platform == 'win32'
        self.has_gps = False
        self.last_decode_time = None
        self.view = MainView(model.main_window_x,
                             model.main_window_y,
                             model.theme,
                             model.park,
                             model.shift,
                             self.win32)
        model.add_event_listener(Callback.QUIT, lambda a: self.view.quit())
        model.add_event_listener(Callback.GPS_DECODE, self.gps_decode)
        model.add_event_listener(Callback.WSJTX_STATUS, self.wsjtx_status)
        model.add_event_listener(Callback.WSJTX_CALLS, self.wsjtx_calls)
        model.add_event_listener(Callback.GPS_OPEN, self.gps_open)
                         
        self.view.protocol('WM_DELETE_WINDOW', model.notify_quit)

        self.view.park_button.configure(command=self.park)

        self.view.shift.bind('<<ComboboxSelected>>', self.shift)

        if self.win32:
            self.view.time_button.configure(command=self.time)
        else:
            self.view.time_button.configure(state = 'disabled')

            
        self.view.grid_button.configure(command=self.do_grid)
        self.view.rx_tx_label.bind('<Double-1>', self.abort_tx)
                    
        self.view.calls_pota.bind('<Double-1>', self.do_call_pota)
        self.view.calls_pota.bind('<Return>', self.do_call_pota)

        self.view.calls_me.bind('<Double-1>', self.do_call_me)
        self.view.calls_me.bind('<Return>', self.do_call_me)

        self.view.calls_cq.bind('<Double-1>', self.do_call_cq)
        self.view.calls_cq.bind('<Return>', self.do_call_cq)

        self.lookup = {self.view.calls_pota: {},
                       self.view.calls_me: {},
                       self.view.calls_cq: {}}
        self.call_data = {self.view.calls_pota: [],
                          self.view.calls_me: [],
                          self.view.calls_cq: []}

    def do_call(self, entry):
        sel = entry.selection()
        if len(sel) > 0:
            index = self.lookup[entry].get(sel[0])
            if index is not None:
                msg = self.call_data[entry][index]
                model.do_call(msg)


    def do_call_pota(self, e):
        self.do_call(self.view.calls_pota)

    def do_call_me(self, e):
        self.do_call(self.view.calls_me)

    def do_call_cq(self, e):
        self.do_call(self.view.calls_cq)

    def gps_open(self, open_):
        if self.view is not None:
            self.has_gps = open_
            if not open_:
                self.view.gps_text.set('No GPS')

    def gps_decode(self, d):
        if self.view is not None:
            if d is str:
                self.view.gps_text.set(d)
            else:
                g = 'N/A' if (dg := d['grid']) is None else dg
                t = 'N/A' if (tg := d['time']) is None else tg
                self.view.gps_text.set(g)
                self.view.time_text.set(t)

    def wsjtx_status(self, d):
        if self.view is not None:
            self.update_rx_tx(d.transmitting, d.tx_msg)

    def do_grid(self):
        model.set_grid()

    def time(self):
        model.set_time()

    def park(self):
        model.set_park(p := self.view.park.get())
        if p == '':
            self.view.shift_text.set(n := '')
            model.shift = n
            self.view.shift['state'] = 'disabled'
        else:
            self.view.shift['state'] = 'readonly'

    def shift(self, _):
        model.shift = self.view.shift_text.get()
        self.view.shift.selection_clear()

    def abort_tx(self, _):
        model.abort_tx()

    def wsjtx_calls(self, d):
        if self.view is not None:
            a = d[0] + d[1] + d[2]
            if len(a) == 0:
                return
            if chg := (a[0].time != self.last_decode_time):
                self.last_decode_time = a[0].time
            for (d, e) in zip(d, (self.view.calls_pota,
                                  self.view.calls_me,
                                  self.view.calls_cq)):
                if (chg):
                    self.call_data[e] = []
                    self.lookup[e] = {}
                    for item in e.get_children():
                        e.delete(item)
                l = len(self.call_data[e])
                self.call_data[e] += d
                for i,j in enumerate(d):
                    k = e.insert(parent='',
                                 index='end',
                                 values=(f"{j.snr:3}",
                                         j.message,))
                    self.lookup[e][k] = i + l

    def update_rx_tx(self, tx, msg=''):
        if self.view is not None:
            self.view.rx_tx.set('TX: ' + msg.strip() if tx else 'RX')

    def notify(self, _):
        while True:
            data = model.pop()
            if data is None:
                break
            id_, d = data
            match id_:
                case NotifyGUI.GPS_OPEN:
                    self.has_gps = True
                    self.view.gps_button.configure(state = 'normal')
                    if self.win32:
                        self.view.time_button.configure(state = 'normal')
                case NotifyGUI.GPS_CLOSE:
                    self.view.gps_text.set('No GPS')
                    self.view.gps_button.configure(state = 'disabled')
                    self.view.time_button.configure(state = 'disabled')
                    self.has_gps = False
                     
    def close(self):
        model.save_main_window_position(self.view.winfo_x(),
                                        self.view.winfo_y())
        self.view.destroy()
        self.view = None

def run():
    if model.platform == 'win32':
        # print(model.gps_serial_address)
        gps = GPSSerial(ProcessID.GPS_SERIAL,
                        model.gps_serial_address,
                        Callback.GPS_SERIAL_SEND)
    else:
        gps = UDPClientController(ProcessID.GPS,
                                  model.gps_address,
                                  Callback.GPS_SEND)
    wsjtx = UDPServerController(ProcessID.WSJTX,
                               model.wsjtx_address,
                               Callback.WSJTX_SEND)
    mc = MainController(ProcessID.MAIN)
    gps.start()
    wsjtx.start()
    mc.view.mainloop()
    mc.close()
    gps.stop()
    wsjtx.stop()
    model.close()

if __name__ == '__main__':
    run()        
        
