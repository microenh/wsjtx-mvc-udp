from library.udp_server_base import UDPServerBase

from library.rx_msg import parse
from library.event import NotifyGUI
from library.wsjtx_db import wsjtx_db
from library.settings import settings
from library.tx_msg import heartbeat

from library.utility import timestamp

# file to save WJST-X data or None
CAPTURE_DATA = None

class WSJTX(UDPServerBase):
    def __init__(self):
        super().__init__(settings.wsjtx_address)
        self.r = []
        self.data_out = None if CAPTURE_DATA is None else open(CAPTURE_DATA, 'w')
        
    def stop(self):
        if self.data_out is not None:
            self.data_out.close()
        super().stop()

    def report(self, open_):
        self.push(NotifyGUI.WSJTX_OPEN if open_ else NotifyGUI.WSJTX_CLOSE)        

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
            elif msg_parse[0] == settings.de_call:
                dx_call = msg_parse[1]
                append = call
            else:
                # print(i.message, msg_parse)
                continue
            if dx_call is not None:    
                if wsjtx_db.exists(dx_call, i) is None:
                    append.append(i)                   
        pota.sort(key=lambda a: a.snr, reverse=True)
        call.sort(key=lambda a: a.snr, reverse=True)
        cq.sort(key=lambda a: a.snr, reverse=True)
        self.push(NotifyGUI.WSJTX_CALLS, (pota, call, cq))
        
    def process(self, data):
        if self.data_out is not None:
            print(f'{data},', file=self.data_out)
        d = parse(data)
        msg_id = d.msg_id
        match msg_id:
            case 0:  # HEARTBEAT
                # print('heartbeat')
                self.push(NotifyGUI.WSJTX_HB)
                self.send(heartbeat())
            case 1:  # STATUS
                # print(f'{timestamp()} decoding: {d.decoding}')
                settings.update_status(d)
                self.push(NotifyGUI.WSJTX_STATUS, d)
                if not d.decoding:
                    self.process_decodes()
                    self.r = []
            case 2:  # DECODE
                self.r.append(d)
            case 5:  # LOG
                wsjtx_db.add(d)
            case 12:  # ADIF
                wsjtx_db.add_log(d.text)
                    


if __name__ == '__main__':
    from main import main
    main()

