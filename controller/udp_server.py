import socket
from struct import pack
from threading import Thread
from model.model import model
from model.event import ProcessID, Callback

class UDPServerController:
    def __init__(self, id_, address, send_event):
        self.id_ = id_
        model.add_event_listener(send_event, self.send)
        self.addr = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1.0)
        self.thread = Thread(target=self.run)
        host = address[0]
        if int(host.split('.')[0]) in range(224,240):
            mreq = pack("4sii",
                       socket.inet_aton(host),
                       socket.INADDR_ANY, 0)
            self.sock.setsockopt(socket.IPPROTO_IP,
                                 socket.IP_ADD_MEMBERSHIP,
                                 mreq)
            host = ''
        self.sock.bind(address)

    def report(self, open_):
        model.notify_state(self.id_, open_)

    def start(self):
        self.thread.start()

    def send(self, data):
        if self.addr is not None:
            self.sock.sendto(data, self.addr)

    def stop(self):
        self.thread.join()
        
    def run(self):
        self.report(True)
        while model.running:
            try:
                data, self.addr = self.sock.recvfrom(1024)
                self.process(data)
            except TimeoutError:
                # print('timeout')
                continue
        self.report(False)

if __name__ == '__main__':
    wsjtx = UDPServerControler(ProcessID.WSJTX,
                               model.settings.wsjtx_address,
                               Callback.WSJTX_SEND)
    wsjtx.start()
