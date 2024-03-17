from model.model import model
from model.event import ProcessID, Callback 
from view.main import MainView

try:
    from udp_client import UDPClientController
    from udp_server import UDPServerController
except ModuleNotFoundError:
    from controller.udp_client import UDPClientController
    from controller.udp_server import UDPServerController

class MainController:
    def __init__(self, id_):

        self.id_ = id_
        self.has_gps = False
        self.last_decode_time = None
        self.view = MainView(*model.main_window_setup)
        model.add_event_listener(Callback.QUIT, lambda a: self.view.quit())
        model.add_event_listener(Callback.GPS_DECODE, self.gps_decode)
        model.add_event_listener(Callback.WSJTX_STATUS, self.wsjtx_status)
        model.add_event_listener(Callback.WSJTX_CALLS, self.wsjtx_calls)
        model.add_event_listener(Callback.GPS_OPEN, self.gps_open)
                         
        self.view.protocol('WM_DELETE_WINDOW', model.notify_quit)
        
        self.view.time_button.configure(command=self.time)
        self.view.socket_button.configure(command=self.socket)
        self.view.grid_button.configure(command=self.do_grid)
        self.view.rx_tx_label.bind('<Double-1>', self.abort_tx)
        for c in (self.view.calls_pota,
                  self.view.calls_me,
                  self.view.calls_cq):
            c.bind('<Double-1>', lambda e: self.do_call(e, c))
            c.bind('<Return>', lambda e: self.do_call(e, c))

        self.lookup = {self.view.calls_pota: {},
                       self.view.calls_me: {},
                       self.view.calls_cq: {}}
        self.call_data = {self.view.calls_pota: [],
                          self.view.calls_me: [],
                          self.view.calls_cq: []}

    def gps_open(self, open_):
        if self.view is not None:
            self.has_gps = open_
            if not open_:
                self.view.gps_text.set('No GPS')
            self.update_gps_buttons()

    def gps_decode(self, d):
        if self.view is not None:
            if d is str:
                self.view.gps_text.set(d)
            else:
                g = 'N/A' if (dg := d['grid']) is None else dg
                t = 'N/A' if (tg := d['time']) is None else '%02d:%02d:%02d' % tg
                self.view.gps_text.set(f'GRID: {g}      TIME: {t}')
                self.update_gps_buttons(dg, tg)

    def wsjtx_status(self, d):
        if self.view is not None:
            self.update_rx_tx(d.transmitting, d.tx_msg)

    def do_grid(self):
        model.set_grid()

    def time(self):
        model.set_time()

    def socket(self):
        self.update_calls()
        
    def abort_tx(self):
        model.abort_tx()

    def do_call(self, _, entry):
        sel = entry.selection()
        if len(sel) > 0:
            index = self.lookup[entry].get(sel[0])
            if index is not None:
                msg = self.call_data[entry][index]
                model.do_call(msg)

    def update_gps_buttons(self, grid=None, time=None):
        if self.view is not None:
            if self.has_gps:
                self.view.time_button.configure(text = 'TIME',
                    state='disabled' if time is None else 'normal')
                self.view.grid_button.configure(text = 'GRID',
                    state='disabled' if grid is None else 'normal')                           
            else:
                self.view.time_button.configure(text = '', state='disabled')
                self.view.grid_button.configure(text = 'GPS')

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
            # print('ID', id_)
            match id_:
                case NotifyGUI.GPS_OPEN:
                    self.has_gps = True
                    self.update_gps_buttons()
                case NotifyGUI.GPS_CLOSE:
                    self.view.gps_text.set('No GPS')
                    self.has_gps = False
                    self.update_gps_buttons()
                     
    def close(self):
        model.save_main_window_position(self.view.winfo_x(),
                                        self.view.winfo_y())
        self.view.destroy()
        self.view = None

def run():
    gps = UDPClientController(ProcessID.GPS,
                              model.settings.gps_address,
                              Callback.GPS_SEND)
    wsjtx = UDPServerController(ProcessID.WSJTX,
                               model.settings.wsjtx_address,
                               Callback.WSJTX_SEND)
    mc = MainController(ProcessID.MAIN)
    gps.start()
    wsjtx.start()
    mc.view.mainloop()
    mc.close()
    model.close()
    gps.stop()
    wsjtx.stop()

if __name__ == '__main__':
    run()        
        
